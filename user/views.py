from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import json
import ssl

from .models import User, EmailVerificationCode


def login_page(request):
    """登录页面"""
    return render(request, 'login.html')


def register_page(request):
    """注册页面"""
    return render(request, 'register.html')


@require_http_methods(["POST"])
@csrf_exempt
def login(request):
    """用户登录"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': '邮箱和密码不能为空'
            })
        
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '用户不存在或已被禁用'
            })
        
        if not user.check_password(password):
            return JsonResponse({
                'success': False,
                'error': '密码错误'
            })
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # 将用户信息存储到session中
        request.session['user_id'] = user.id
        request.session['user_name'] = user.name
        request.session['user_email'] = user.email
        
        return JsonResponse({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'avatar': user.avatar or ''
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '请求数据格式错误'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["POST"])
@csrf_exempt
def register(request):
    """用户注册"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # 验证输入
        if not name or not email or not password:
            return JsonResponse({
                'success': False,
                'error': '所有字段都不能为空'
            })
        
        if not verification_code:
            return JsonResponse({
                'success': False,
                'error': '请输入验证码'
            })
        
        if len(name) < 2 or len(name) > 20:
            return JsonResponse({
                'success': False,
                'error': '用户名长度必须在2-20个字符之间'
            })
        
        if len(password) < 6:
            return JsonResponse({
                'success': False,
                'error': '密码长度不能少于6位'
            })
        
        if password != confirm_password:
            return JsonResponse({
                'success': False,
                'error': '两次输入的密码不一致'
            })
        
        # 检查用户名是否已存在
        if User.objects.filter(name=name).exists():
            return JsonResponse({
                'success': False,
                'error': '用户名已存在'
            })
        
        # 检查邮箱是否已存在
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': '邮箱已被注册'
            })
        
        # 验证验证码
        try:
            code_obj = EmailVerificationCode.objects.filter(
                email=email,
                code=verification_code,
                purpose='register',
                is_used=False
            ).order_by('-created_at').first()
            
            if not code_obj:
                return JsonResponse({
                    'success': False,
                    'error': '验证码错误'
                })
            
            if code_obj.is_expired():
                return JsonResponse({
                    'success': False,
                    'error': '验证码已过期，请重新获取'
                })
            
            # 标记验证码为已使用
            code_obj.is_used = True
            code_obj.save()
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'验证码验证失败：{str(e)}'
            })
        
        # 创建新用户
        user = User.objects.create(
            name=name,
            email=email
        )
        user.set_password(password)
        user.save()
        
        # 自动登录
        request.session['user_id'] = user.id
        request.session['user_name'] = user.name
        request.session['user_email'] = user.email
        
        return JsonResponse({
            'success': True,
            'message': '注册成功',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'avatar': user.avatar or ''
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '请求数据格式错误'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["POST"])
@csrf_exempt
def logout(request):
    """用户登出"""
    try:
        # 清除session
        request.session.flush()
        
        return JsonResponse({
            'success': True,
            'message': '登出成功'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["GET"])
def get_user_info(request):
    """获取当前用户信息"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': '用户未登录'
            })
        
        try:
            user = User.objects.get(id=user_id, is_active=True)
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'avatar': user.avatar or ''
                }
            })
        except User.DoesNotExist:
            # 用户不存在，清除session
            request.session.flush()
            return JsonResponse({
                'success': False,
                'error': '用户不存在'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["POST"])
@csrf_exempt
def send_verification_code(request):
    """发送邮箱验证码"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        purpose = data.get('purpose', 'register').strip()  # 默认是注册
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': '邮箱不能为空'
            })
        
        # 检查邮箱格式
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'error': '邮箱格式不正确'
            })
        
        # 如果是注册，检查邮箱是否已被注册
        if purpose == 'register':
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': '该邮箱已被注册'
                })
        
        # 检查是否在1分钟内发送过验证码（防止频繁发送）
        recent_code = EmailVerificationCode.objects.filter(
            email=email,
            purpose=purpose,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).first()
        
        if recent_code:
            return JsonResponse({
                'success': False,
                'error': '验证码发送过于频繁，请稍后再试'
            })
        
        # 生成验证码
        code = EmailVerificationCode.generate_code()
        
        # 将之前的验证码标记为已使用
        EmailVerificationCode.objects.filter(
            email=email,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)
        
        # 保存新的验证码
        verification_code = EmailVerificationCode.objects.create(
            email=email,
            code=code,
            purpose=purpose
        )
        
        # 发送邮件
        try:
            subject = '暮雪 - 邮箱验证码'
            message = f'''
            您好！
            
            您的验证码是：{code}
            
            验证码有效期为10分钟，请勿泄露给他人。
            
            如果这不是您的操作，请忽略此邮件。
            
            暮雪团队
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'success': True,
                'message': '验证码已发送到您的邮箱，请查收'
            })
        except Exception as e:
            # 如果邮件发送失败，删除验证码记录
            verification_code.delete()
            return JsonResponse({
                'success': False,
                'error': f'邮件发送失败：{str(e)}'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '请求数据格式错误'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
import random
import string
from datetime import timedelta


class User(models.Model):
    """自定义用户模型"""
    name = models.CharField(max_length=100, verbose_name='用户名', unique=True)
    email = models.EmailField(unique=True, verbose_name='邮箱')
    password = models.CharField(max_length=255, verbose_name='密码')
    avatar = models.URLField(blank=True, null=True, verbose_name='头像')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    is_admin = models.BooleanField(default=False, verbose_name='是否管理员')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='最后登录时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        """设置密码"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """验证密码"""
        return check_password(raw_password, self.password)

    def is_authenticated(self):
        """检查用户是否已认证"""
        return self.is_active

    def get_short_name(self):
        """获取用户简称"""
        return self.name

    def get_full_name(self):
        """获取用户全名"""
        return self.name


class EmailVerificationCode(models.Model):
    """邮箱验证码模型"""
    email = models.EmailField(verbose_name='邮箱')
    code = models.CharField(max_length=6, verbose_name='验证码')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_used = models.BooleanField(default=False, verbose_name='是否已使用')
    purpose = models.CharField(max_length=20, default='register', verbose_name='用途')  # register, reset_password等

    class Meta:
        verbose_name = '邮箱验证码'
        verbose_name_plural = '邮箱验证码'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_used', 'created_at']),
        ]

    def __str__(self):
        return f'{self.email} - {self.code}'

    @staticmethod
    def generate_code():
        """生成6位数字验证码"""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        """检查验证码是否过期（10分钟）"""
        return timezone.now() - self.created_at > timedelta(minutes=10)

    def is_valid(self):
        """检查验证码是否有效（未使用且未过期）"""
        return not self.is_used and not self.is_expired()
import os
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
import mimetypes
from pathlib import Path


def download_center(request):
    """下载中心主页面"""
    # 获取resources目录下的所有子目录
    resources_path = os.path.join(settings.BASE_DIR, 'resources')
    categories = []
    
    if os.path.exists(resources_path):
        for item in os.listdir(resources_path):
            item_path = os.path.join(resources_path, item)
            if os.path.isdir(item_path):
                categories.append({
                    'name': item,
                    'path': item,
                    'file_count': len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                })
    
    # 按名称排序
    categories.sort(key=lambda x: x['name'])
    
    context = {
        'categories': categories,
        'selected_category': request.GET.get('category', ''),
    }
    return render(request, 'download_center.html', context)


def category_files(request, category_name):
    """获取指定分类下的所有文件"""
    resources_path = os.path.join(settings.BASE_DIR, 'resources', category_name)
    
    if not os.path.exists(resources_path) or not os.path.isdir(resources_path):
        return JsonResponse({'error': '分类不存在'}, status=404)
    
    files = []
    for filename in os.listdir(resources_path):
        file_path = os.path.join(resources_path, filename)
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            files.append({
                'name': filename,
                'size': file_size,
                'size_display': format_file_size(file_size),
                'extension': os.path.splitext(filename)[1].lower()
            })
    
    # 按文件名排序
    files.sort(key=lambda x: x['name'])
    
    return JsonResponse({'files': files})


def download_file(request, category_name, filename):
    """下载文件"""
    # 构建文件路径
    file_path = os.path.join(settings.BASE_DIR, 'resources', category_name, filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("文件不存在")
    
    # 获取文件MIME类型
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # 读取文件内容
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


def format_file_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

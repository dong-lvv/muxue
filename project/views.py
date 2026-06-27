from django.shortcuts import render, get_object_or_404
from .models import Project

def project_list(request):
    """
    项目主页：展示所有已发布项目列表
    """
    projects = Project.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'project_list.html', {'projects': projects})

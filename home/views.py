from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import Action
from blog.models import Category, Article
from user.models import User
from project.models import Project

def index(request):
    """首页视图 - 重定向到home"""
    return redirect('home')


def home(request):
    """首页视图 - 嵌入式学习平台主页"""
    categories = Category.objects.filter(is_active=True).order_by('order', 'id')
    featured_articles = Article.objects.filter(
        is_published=True, is_featured=True
    ).select_related('category').order_by('-published_at')[:3]
    latest_articles = Article.objects.filter(
        is_published=True
    ).select_related('category').order_by('-published_at')[:6]

    context = {
        'actions': Action.objects.all()[:5],
        'categories': categories,
        'featured_articles': featured_articles,
        'latest_articles': latest_articles,
        'article_count': Article.objects.filter(is_published=True).count(),
        'project_count': Project.objects.filter(is_published=True).count(),
        'category_count': categories.count(),
        'total_views': Article.objects.filter(is_published=True).aggregate(
            total=Sum('view_count')
        )['total'] or 0,
        'total_users': User.objects.count(),
    }
    return render(request, 'home.html', context)

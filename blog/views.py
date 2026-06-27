from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
from .models import Category, Article, ArticleImage
import json
import markdown
import re
from django.conf import settings


def blog(request):
    """博客页面视图"""
    categories = Category.objects.filter(is_active=True).order_by('order', 'id')
    context = {
        'categories': categories
    }
    return render(request, 'blog.html', context)


def article_detail(request, article_id):
    """文章详情页面"""
    article = get_object_or_404(Article, id=article_id, is_published=True)
    article.increment_view_count()

    # 预处理：将 Markdown/HTML 内的相对图片路径重写为 MEDIA 下的实际可访问路径
    # 约定：文章相关资源存放在 MEDIA_ROOT/blog/<article_id>/ ...，页面访问为 /media/blog/<article_id>/...
    def rewrite_relative_image_urls(text, base_prefix):
        def md_replacer(match):
            alt = match.group(1)
            path = match.group(2).strip()
            if path.startswith('http://') or path.startswith('https://') or path.startswith('/'):
                return match.group(0)
            return f'![{alt}]({base_prefix}{path})'

        text = re.sub(r'!\[(.*?)\]\(([^)]+)\)', md_replacer, text)

        def html_replacer(match):
            before = match.group(1)
            src = match.group(2).strip()
            if src.startswith('http://') or src.startswith('https://') or src.startswith('/'):
                return match.group(0)
            return f'<img{before}src="{base_prefix}{src}"'

        text = re.sub(r'<img([^>]+)src=["\']([^"\']+)["\']', html_replacer, text, flags=re.IGNORECASE)
        return text

    base_media_prefix = f'{settings.MEDIA_URL}blog/{article.id}/'
    preprocessed_markdown = rewrite_relative_image_urls(article.content, base_media_prefix)

    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code'
    ])
    article.content_html = mark_safe(md.convert(preprocessed_markdown))

    context = {'article': article}
    return render(request, 'article_detail.html', context)


@require_http_methods(["GET"])
def get_articles_by_category(request, category_id):
    """根据分类ID获取文章列表"""
    try:
        category = get_object_or_404(Category, id=category_id, is_active=True)
        articles = Article.objects.filter(
            category=category,
            is_published=True
        ).order_by('-published_at', '-created_at')

        articles_data = []
        for article in articles:
            clean_content = re.sub(r'[#*`\[\]()]', '', article.content)
            clean_content = re.sub(r'\n+', ' ', clean_content)
            summary = clean_content[:100] + '...' if len(clean_content) > 100 else clean_content

            articles_data.append({
                'id': article.id,
                'title': article.title,
                'summary': summary,
                'view_count': article.view_count,
                'published_at': article.published_at.strftime('%Y-%m-%d'),
                'is_featured': article.is_featured
            })

        return JsonResponse({
            'success': True,
            'category_name': category.name,
            'articles': articles_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def get_article_detail(request, article_id):
    """获取文章详情"""
    try:
        article = get_object_or_404(Article, id=article_id, is_published=True)
        article.increment_view_count()

        return JsonResponse({
            'success': True,
            'article': {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'view_count': article.view_count,
                'published_at': article.published_at.strftime('%Y-%m-%d %H:%M'),
                'category_name': article.category.name
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def search_articles(request):
    """搜索文章"""
    try:
        keyword = request.GET.get('q', '').strip()

        if not keyword:
            return JsonResponse({'success': False, 'error': '搜索关键词不能为空'})

        articles = Article.objects.filter(
            title__icontains=keyword,
            is_published=True
        ).order_by('-published_at', '-created_at')

        articles_data = []
        for article in articles:
            clean_content = re.sub(r'[#*`\[\]()]', '', article.content)
            clean_content = re.sub(r'\n+', ' ', clean_content)
            summary = clean_content[:100] + '...' if len(clean_content) > 100 else clean_content

            articles_data.append({
                'id': article.id,
                'title': article.title,
                'summary': summary,
                'view_count': article.view_count,
                'published_at': article.published_at.strftime('%Y-%m-%d'),
                'is_featured': article.is_featured
            })

        return JsonResponse({
            'success': True,
            'articles': articles_data,
            'keyword': keyword,
            'count': len(articles_data)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== Admin 拖拽批量上传 ====================

@csrf_exempt
@require_http_methods(["POST"])
def upload_article_images(request, article_id):
    """批量上传文章配图（拖拽上传专用）"""
    article = get_object_or_404(Article, id=article_id)
    files = request.FILES.getlist('images')

    if not files:
        return JsonResponse({'success': False, 'error': '没有选择文件'})

    uploaded = []
    failed = []
    for f in files:
        try:
            img = ArticleImage.objects.create(article=article, image=f, caption='')
            uploaded.append({
                'id': img.id,
                'filename': img.filename(),
                'url': img.image.url,
            })
        except Exception as e:
            failed.append({'filename': f.name, 'error': str(e)})

    return JsonResponse({
        'success': True,
        'uploaded': uploaded,
        'failed': failed,
        'total': len(uploaded),
    })

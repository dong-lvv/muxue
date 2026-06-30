from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from .models import Category, Article, ArticleImage
import json
import os
import posixpath
import markdown
import re
from django.conf import settings


def blog(request):
    """博客页面视图"""
    categories = Category.objects.filter(is_active=True).order_by('order', 'id')
    featured_articles = Article.objects.filter(
        is_published=True,
        is_featured=True,
    ).select_related('category').order_by('-published_at', '-created_at')
    recent_articles = Article.objects.filter(
        is_published=True,
    ).select_related('category').order_by('-updated_at', '-published_at')[:3]
    context = {
        'categories': categories,
        'featured_articles': featured_articles,
        'recent_articles': recent_articles,
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
                'category_name': article.category.name,
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
                'category_name': article.category.name,
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


# ==================== Admin 笔记文件夹导入 ====================

ALLOWED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'}


def _normalize_rel_path(p: str) -> str:
    """统一成 posix 风格、去掉开头的 ./"""
    if not p:
        return ''
    p = p.replace('\\', '/')
    while p.startswith('./'):
        p = p[2:]
    return p


def _rewrite_image_refs_in_markdown(text, saved_images):
    """把 md 中对图片的相对引用改写到 img/<basename>。

    saved_images: List[Tuple[rel_in_upload, basename_saved]]
    匹配策略：以引用路径的 basename 命中。外链 / 绝对路径不动。
    """
    if not saved_images:
        return text

    by_basename = {}
    for rel, base in saved_images:
        by_basename[os.path.basename(rel)] = base

    def is_external(p):
        return p.startswith('http://') or p.startswith('https://') or p.startswith('/')

    def md_replacer(m):
        alt = m.group(1)
        path = m.group(2).strip()
        if is_external(path):
            return m.group(0)
        base = posixpath.basename(path.replace('\\', '/'))
        if base in by_basename:
            return f'![{alt}](img/{by_basename[base]})'
        return m.group(0)

    text = re.sub(r'!\[(.*?)\]\(([^)]+)\)', md_replacer, text)

    def html_replacer(m):
        before = m.group(1)
        src = m.group(2).strip()
        if is_external(src):
            return m.group(0)
        base = posixpath.basename(src.replace('\\', '/'))
        if base in by_basename:
            return f'<img{before}src="img/{by_basename[base]}"'
        return m.group(0)

    text = re.sub(r'<img([^>]+)src=["\']([^"\']+)["\']', html_replacer, text, flags=re.IGNORECASE)
    return text


@staff_member_required
def import_note(request):
    """导入一个笔记文件夹：一个 .md + 同级 img/ 目录里的图片。"""
    categories = Category.objects.filter(is_active=True).order_by('order', 'id')

    if request.method == 'GET':
        return render(request, 'admin/blog/import_note.html', {
            'categories': categories,
            'title': '导入笔记文件夹',
        })

    try:
        category_id = request.POST.get('category_id')
        title_override = request.POST.get('title', '').strip()
        is_published = request.POST.get('is_published') == '1'
        is_featured = request.POST.get('is_featured') == '1'

        if not category_id:
            return JsonResponse({'success': False, 'error': '请选择文章分类'})
        try:
            category = Category.objects.get(pk=category_id, is_active=True)
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': '分类不存在或已禁用'})

        md_file = request.FILES.get('markdown')
        if not md_file:
            return JsonResponse({'success': False, 'error': '没有找到 Markdown 文件'})
        if not md_file.name.lower().endswith('.md'):
            return JsonResponse({'success': False, 'error': 'Markdown 文件必须以 .md 结尾'})

        md_bytes = md_file.read()
        try:
            md_text = md_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                md_text = md_bytes.decode('gbk')
            except Exception:
                return JsonResponse({'success': False, 'error': 'Markdown 文件编码无法识别（请使用 UTF-8 / GBK）'})

        if title_override:
            title = title_override
        else:
            title = os.path.splitext(os.path.basename(md_file.name))[0]

        image_files = request.FILES.getlist('images')
        image_paths = request.POST.getlist('image_paths')
        if len(image_paths) != len(image_files):
            image_paths = [f.name for f in image_files]

        article = Article.objects.create(
            title=title,
            content=md_text,
            category=category,
            is_published=is_published,
            is_featured=is_featured,
        )

        saved_images = []
        seen_basenames = {}
        skipped = []
        for f, rel in zip(image_files, image_paths):
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXT:
                skipped.append(f.name)
                continue
            rel_norm = _normalize_rel_path(rel) or f.name
            base = os.path.basename(rel_norm)

            if base in seen_basenames:
                seen_basenames[base] += 1
                stem, e = os.path.splitext(base)
                base = f'{stem}_{seen_basenames[base]}{e}'
            else:
                seen_basenames[base] = 0

            f.name = base
            ArticleImage.objects.create(article=article, image=f, caption='')
            saved_images.append((rel_norm, base))

        if saved_images:
            new_content = _rewrite_image_refs_in_markdown(article.content, saved_images)
            if new_content != article.content:
                article.content = new_content
                article.save(update_fields=['content'])

        return JsonResponse({
            'success': True,
            'article_id': article.id,
            'title': article.title,
            'image_count': len(saved_images),
            'skipped': skipped,
            'admin_url': reverse('admin:blog_article_change', args=[article.id]),
            'view_url': reverse('article_detail', args=[article.id]),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'导入失败: {e}'})

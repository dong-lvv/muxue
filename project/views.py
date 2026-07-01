import markdown
import re
import json
import os
import posixpath
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.conf import settings

from .models import Project, ProjectDocument, ProjectDocumentImage


def project_list(request):
    projects = Project.objects.filter(is_published=True).prefetch_related('tags')
    return render(request, 'project_list.html', {'projects': projects})


def project_detail(request, project_id):
    project = get_project(project_id)
    project.increment_view_count()
    return render_project_detail(request, project)


def project_document_detail(request, project_id, document_id):
    project = get_project(project_id)
    document = get_object_or_404(
        ProjectDocument,
        id=document_id,
        project=project,
        is_published=True,
    )

    # 预处理图片路径
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

    base_media_prefix = f'{settings.MEDIA_URL}project/{document.id}/'
    preprocessed_markdown = rewrite_relative_image_urls(document.content, base_media_prefix)

    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.toc',
    ])
    document.content_html = mark_safe(md.convert(preprocessed_markdown))
    return render_project_detail(request, project, document)


def get_project(project_id):
    return get_object_or_404(
        Project.objects.prefetch_related('tags', 'updates', 'documents'),
        id=project_id,
        is_published=True,
    )


def render_project_detail(request, project, active_document=None):
    documents = project.documents.filter(is_published=True).order_by('order', 'created_at', 'id')
    updates = project.updates.all()
    return render(request, 'project_detail.html', {
        'project': project,
        'documents': documents,
        'updates': updates,
        'active_document': active_document,
    })


def render_markdown(content):
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.toc',
    ])
    return md.convert(content)


@csrf_exempt
@require_http_methods(["POST"])
def upload_project_document_images(request, document_id):
    """批量上传项目文档配图（拖拽上传专用）"""
    document = get_object_or_404(ProjectDocument, id=document_id)
    files = request.FILES.getlist('images')

    if not files:
        return JsonResponse({'success': False, 'error': '没有选择文件'})

    uploaded = []
    failed = []
    for f in files:
        try:
            img = ProjectDocumentImage.objects.create(document=document, image=f, caption='')
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
    """把 md 中对图片的相对引用改写到 img/<basename>。"""
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
def import_project_note(request):
    """导入一个笔记文件夹：一个 .md + 同级 img/ 目录里的图片。"""
    projects = Project.objects.filter(is_published=True)

    if request.method == 'GET':
        return render(request, 'admin/project/import_note.html', {
            'projects': projects,
            'title': '导入笔记文件夹',
        })

    try:
        project_id = request.POST.get('project_id')
        title_override = request.POST.get('title', '').strip()
        is_published = request.POST.get('is_published') == '1'

        if not project_id:
            return JsonResponse({'success': False, 'error': '请选择所属项目'})
        try:
            project = Project.objects.get(pk=project_id, is_published=True)
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': '项目不存在或未发布'})

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

        document = ProjectDocument.objects.create(
            project=project,
            title=title,
            content=md_text,
            is_published=is_published,
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
            ProjectDocumentImage.objects.create(document=document, image=f, caption='')
            saved_images.append((rel_norm, base))

        if saved_images:
            new_content = _rewrite_image_refs_in_markdown(document.content, saved_images)
            if new_content != document.content:
                document.content = new_content
                document.save(update_fields=['content'])

        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'title': document.title,
            'image_count': len(saved_images),
            'skipped': skipped,
            'admin_url': reverse('admin:project_projectdocument_change', args=[document.id]),
            'view_url': reverse('project:project_document_detail', args=[project.id, document.id]),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'导入失败: {e}'})

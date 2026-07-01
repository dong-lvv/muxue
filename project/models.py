import os
from django.db import models
from django.utils import timezone


def project_document_image_path(instance, filename):
    """上传到 media/project/{文档ID}/img/文件名"""
    return os.path.join('project', str(instance.document.id), 'img', filename)


class ProjectTag(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name='标签名称')
    color = models.CharField(
        max_length=7,
        default="#afcdda",
        verbose_name='标签颜色',
        help_text='HEX 格式，例如 #5b8cbd',
    )

    class Meta:
        verbose_name = '项目标签'
        verbose_name_plural = '项目标签'
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200, verbose_name='项目标题')
    summary = models.TextField(blank=True, default='', verbose_name='项目简介')
    bilibili_url = models.URLField(blank=True, default='', verbose_name='Bilibili 视频链接')
    github_url = models.URLField(blank=True, default='', verbose_name='GitHub 开源链接')
    started_at = models.DateField(default=timezone.now, verbose_name='项目开始时间')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_published = models.BooleanField(default=True, verbose_name='是否发布')
    view_count = models.PositiveIntegerField(default=0, verbose_name='浏览次数')
    tags = models.ManyToManyField(ProjectTag, related_name='projects', blank=True, verbose_name='项目标签')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'
        ordering = ['order', '-started_at', '-updated_at']

    def __str__(self):
        return self.title

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents', verbose_name='所属项目')
    title = models.CharField(max_length=200, verbose_name='文档标题')
    summary = models.TextField(blank=True, default='', verbose_name='文档摘要')
    content = models.TextField(verbose_name='Markdown 内容')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_published = models.BooleanField(default=True, verbose_name='是否发布')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目文档'
        verbose_name_plural = '项目文档'
        ordering = ['order', 'created_at', 'id']

    def __str__(self):
        return f'{self.project.title} - {self.title}'


class ProjectDocumentImage(models.Model):
    """项目文档配图，上传到 media/project/{文档ID}/img/"""
    document = models.ForeignKey(
        ProjectDocument, on_delete=models.CASCADE,
        related_name='images', verbose_name='所属文档'
    )
    image = models.ImageField(
        upload_to=project_document_image_path, verbose_name='图片文件'
    )
    caption = models.CharField(
        max_length=200, blank=True, default='', verbose_name='图片说明'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, verbose_name='上传时间'
    )

    class Meta:
        verbose_name = '项目文档配图'
        verbose_name_plural = '项目文档配图'
        ordering = ['uploaded_at']

    def __str__(self):
        return self.image.name.split('/')[-1] if self.image else '无图片'

    def filename(self):
        return os.path.basename(self.image.name)


class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates', verbose_name='所属项目')
    happened_at = models.DateTimeField(default=timezone.now, verbose_name='更新时间')
    content = models.TextField(blank=True, default='', verbose_name='更新说明')

    class Meta:
        verbose_name = '项目更新'
        verbose_name_plural = '项目更新'
        ordering = ['-happened_at', '-id']

    def __str__(self):
        return f'{self.project.title} - {self.happened_at.strftime("%Y-%m-%d %H:%M")}'

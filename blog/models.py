import os
from django.db import models
from django.utils import timezone


def article_image_path(instance, filename):
    """上传到 media/blog/{文章ID}/img/文件名"""
    return os.path.join('blog', str(instance.article.id), 'img', filename)

class Category(models.Model):
    """博客分类模型"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='分类描述')
    icon = models.CharField(max_length=50, default='fa-folder', verbose_name='图标类名')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '博客分类'
        verbose_name_plural = '博客分类'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class Article(models.Model):
    """博客文章模型"""
    title = models.CharField(max_length=200, verbose_name='文章标题')
    content = models.TextField(verbose_name='文章内容')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles', verbose_name='所属分类')
    view_count = models.PositiveIntegerField(default=0, verbose_name='阅读量')
    is_published = models.BooleanField(default=True, verbose_name='是否发布')
    is_featured = models.BooleanField(default=False, verbose_name='是否推荐')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='发布时间')

    class Meta:
        verbose_name = '博客文章'
        verbose_name_plural = '博客文章'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def increment_view_count(self):
        """增加阅读量"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class ArticleImage(models.Model):
    """文章配图，上传到 media/blog/{文章ID}/img/"""
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE,
        related_name='images', verbose_name='所属文章'
    )
    image = models.ImageField(
        upload_to=article_image_path, verbose_name='图片文件'
    )
    caption = models.CharField(
        max_length=200, blank=True, default='', verbose_name='图片说明'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, verbose_name='上传时间'
    )

    class Meta:
        verbose_name = '文章配图'
        verbose_name_plural = '文章配图'
        ordering = ['uploaded_at']

    def __str__(self):
        return self.image.name.split('/')[-1] if self.image else '无图片'

    def filename(self):
        return os.path.basename(self.image.name)
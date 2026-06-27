from django.db import models

class TechTag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="标签名称")
    color = models.CharField(
        max_length=7,
        default="#2196F3",
        verbose_name="标签颜色",
        help_text="标签颜色（HEX 格式，例如 #FF5733）"
    )

    class Meta:
        verbose_name = "技术标签"
        verbose_name_plural = "技术标签"
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200, verbose_name="项目标题")
    content = models.TextField(verbose_name='内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_published = models.BooleanField(default=True, verbose_name="是否发布")
    tags = models.ManyToManyField('TechTag', related_name='projects', blank=True, verbose_name="技术标签")
    view_count = models.PositiveIntegerField(default=0, verbose_name='阅读量')
    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目展示"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
from django.db import models

# Create your models here.
class Action(models.Model):
    content = models.TextField(verbose_name="内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    def __str__(self):
        return self.content[:20]

    class Meta:
        verbose_name = "动态内容"
        verbose_name_plural = "动态内容"
        ordering = ['-created_at']
import os
import shutil
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Article


@receiver(post_save, sender=Article)
def ensure_article_media_dir(sender, instance, created, **kwargs):
	# 无论创建或更新，都确保基础目录存在；首次创建时会自动生成
	base_dir = os.path.join(settings.MEDIA_ROOT, 'blog', str(instance.id), 'img')
	os.makedirs(base_dir, exist_ok=True)

@receiver(post_delete, sender=Article)
def delete_article_media_dir(sender, instance, **kwargs):
	# 删除整篇文章的媒体目录：media/blog/<id>（包含 img 子目录）
	base_dir = os.path.join(settings.MEDIA_ROOT, 'blog', str(instance.id))
	if os.path.isdir(base_dir):
		shutil.rmtree(base_dir, ignore_errors=True)



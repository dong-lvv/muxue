import os
import shutil
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ProjectDocument


@receiver(post_save, sender=ProjectDocument)
def ensure_project_document_media_dir(sender, instance, created, **kwargs):
    # 确保基础目录存在
    base_dir = os.path.join(settings.MEDIA_ROOT, 'project', str(instance.id), 'img')
    os.makedirs(base_dir, exist_ok=True)

@receiver(post_delete, sender=ProjectDocument)
def delete_project_document_media_dir(sender, instance, **kwargs):
    # 删除整个媒体目录：media/project/<id>
    base_dir = os.path.join(settings.MEDIA_ROOT, 'project', str(instance.id))
    if os.path.isdir(base_dir):
        shutil.rmtree(base_dir, ignore_errors=True)

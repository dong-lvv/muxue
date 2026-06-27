from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    
    def ready(self):
    	# 导入信号以确保注册 post_save 钩子
    	from . import signals  # noqa
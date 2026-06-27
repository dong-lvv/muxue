from django.contrib import admin
from .models import Category, Article, ArticleImage


class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 3
    fields = ['image', 'caption']
    verbose_name = '文章配图'
    verbose_name_plural = '📷 上传文章配图（子目录默认 img）'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'view_count', 'is_published', 'published_at']
    list_filter = ['category', 'is_published', 'is_featured', 'published_at']
    search_fields = ['title', 'content']
    ordering = ['-published_at']
    date_hierarchy = 'published_at'
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    inlines = [ArticleImageInline]
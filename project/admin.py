from django.contrib import admin
from .models import Project, TechTag
from django.utils.html import format_html
# Register your models here.

@admin.register(TechTag)
class TechTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored_display')
    search_fields = ('name',)

    def colored_display(self, obj):
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:4px;">{}</span>',
            obj.color,
            obj.color
        )
    colored_display.short_description = "颜色示例"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_published', 'thumbnail_preview')
    list_filter = ('is_published', 'created_at', 'tags')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)  # 让多选标签更友好
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="width:100px; height:auto;" />', obj.thumbnail.url)
        return "无封面"
    thumbnail_preview.short_description = "封面预览"
from django.contrib import admin
from django.utils.html import format_html

from .models import Project, ProjectDocument, ProjectTag, ProjectUpdate, ProjectDocumentImage


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_preview')
    search_fields = ('name',)

    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:6px;">'
            '<span style="width:14px;height:14px;border-radius:50%;background:{};display:inline-block;"></span>{}'
            '</span>',
            obj.color,
            obj.color,
        )
    color_preview.short_description = '颜色'


class ProjectDocumentInline(admin.StackedInline):
    model = ProjectDocument
    extra = 1
    fields = ('title', 'summary', 'content', 'order', 'is_published')


class ProjectUpdateInline(admin.TabularInline):
    model = ProjectUpdate
    extra = 1
    fields = ('happened_at', 'content')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'started_at', 'order', 'is_published', 'view_count', 'updated_at')
    list_filter = ('is_published', 'started_at', 'tags')
    search_fields = ('title', 'summary')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at', 'view_count')
    date_hierarchy = 'started_at'
    ordering = ('order', '-started_at')
    inlines = [ProjectDocumentInline, ProjectUpdateInline]


class ProjectDocumentImageInline(admin.TabularInline):
    model = ProjectDocumentImage
    extra = 3
    fields = ['image', 'caption']
    verbose_name = '文档配图'
    verbose_name_plural = '📷 上传文档配图（子目录默认 img）'


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'order', 'is_published', 'updated_at')
    list_filter = ('project', 'is_published', 'updated_at')
    search_fields = ('title', 'summary', 'content', 'project__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('project', 'order', 'created_at')
    change_list_template = 'admin/project/projectdocument/change_list.html'
    change_form_template = 'admin/project/projectdocument/change_form.html'

    def get_inlines(self, request, obj=None):
        return [ProjectDocumentImageInline] if obj else []


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ('project', 'happened_at')
    list_filter = ('project', 'happened_at')
    search_fields = ('project__title', 'content')
    ordering = ('-happened_at',)

from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'is_admin', 'created_at', 'last_login']
    list_filter = ['is_active', 'is_admin', 'created_at']
    search_fields = ['name', 'email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'email', 'avatar')
        }),
        ('权限设置', {
            'fields': ('is_active', 'is_admin')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑现有用户
            return self.readonly_fields + ['password']
        return self.readonly_fields
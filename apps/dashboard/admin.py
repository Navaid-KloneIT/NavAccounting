from django.contrib import admin

from .models import Alert, DashboardWidgetConfig


@admin.register(DashboardWidgetConfig)
class DashboardWidgetConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'widget_type', 'position', 'is_visible')
    list_filter = ('widget_type', 'is_visible', 'tenant')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'alert_type', 'tenant', 'is_read', 'created_at')
    list_filter = ('severity', 'is_read', 'tenant')
    search_fields = ('title', 'message')

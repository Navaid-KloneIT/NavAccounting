from django.contrib import admin

from .models import Permission, Role, TenantUserRole


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'module')
    list_filter = ('module',)
    search_fields = ('codename', 'name')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'is_system_role')
    list_filter = ('is_system_role', 'tenant')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)


@admin.register(TenantUserRole)
class TenantUserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'tenant', 'assigned_at')
    list_filter = ('tenant', 'role')
    search_fields = ('user__email', 'role__name')

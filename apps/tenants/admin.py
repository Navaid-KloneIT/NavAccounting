from django.contrib import admin

from .models import Tenant, TenantMembership


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'is_default', 'joined_at')
    list_filter = ('is_default', 'tenant')
    search_fields = ('user__email', 'tenant__name')

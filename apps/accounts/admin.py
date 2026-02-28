from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, UserInvitation, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'avatar', 'last_active_tenant'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'job_title', 'department')
    list_filter = ('tenant',)
    search_fields = ('user__email', 'job_title')


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'tenant', 'invited_by', 'is_accepted', 'expires_at')
    list_filter = ('is_accepted', 'tenant')
    search_fields = ('email',)

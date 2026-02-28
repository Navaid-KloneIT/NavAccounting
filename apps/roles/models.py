from django.conf import settings
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager


class Permission(models.Model):
    """System-wide permission definitions (not tenant-specific)."""
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    module = models.CharField(max_length=100)

    class Meta:
        ordering = ['module', 'codename']

    def __str__(self):
        return f"{self.module}: {self.name}"


class Role(TenantAwareModel):
    """Tenant-specific role definition."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_system_role = models.BooleanField(default=False)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        unique_together = ('name', 'tenant')
        ordering = ['name']

    def __str__(self):
        return self.name


class TenantUserRole(TenantAwareModel):
    """Assigns a role to a user within a tenant."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        unique_together = ('user', 'role', 'tenant')

    def __str__(self):
        return f"{self.user} - {self.role} ({self.tenant})"

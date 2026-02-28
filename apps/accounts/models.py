import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TenantAwareModel
from apps.tenants.managers import TenantAwareManager

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """Extended user model with email as the primary login identifier."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    last_active_tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return self.get_full_name() or self.email

    def get_display_name(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email


class UserProfile(TenantAwareModel):
    """Tenant-specific user profile. A user has a different profile per tenant."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profiles'
    )
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        unique_together = ('user', 'tenant')

    def __str__(self):
        return f"{self.user} - {self.tenant}"


class UserInvitation(TenantAwareModel):
    """Invite a user to join a tenant."""
    email = models.EmailField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    role = models.ForeignKey(
        'roles.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    objects = TenantAwareManager()
    unscoped = models.Manager()

    class Meta:
        unique_together = ('email', 'tenant')

    def __str__(self):
        return f"Invitation for {self.email} to {self.tenant}"

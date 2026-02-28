from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tenants.models import TenantMembership

from .models import UserProfile


@receiver(post_save, sender=TenantMembership)
def create_user_profile_on_membership(sender, instance, created, **kwargs):
    """Auto-create a tenant-specific user profile when a user joins a tenant."""
    if created:
        UserProfile.unscoped.get_or_create(
            user=instance.user,
            tenant=instance.tenant,
            defaults={
                'job_title': '',
                'department': '',
            }
        )

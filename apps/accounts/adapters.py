from allauth.account.adapter import DefaultAccountAdapter
from django.utils.text import slugify

from apps.tenants.models import Tenant, TenantMembership


class NavAccountingAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """After user creation, auto-create their first tenant."""
        user = super().save_user(request, user, form, commit=False)
        user.save()

        # Create default tenant for the user
        base_slug = slugify(f"{user.username}-company")
        slug = base_slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = Tenant.objects.create(
            name=f"{user.first_name or user.username}'s Company",
            slug=slug,
            owner=user,
        )
        TenantMembership.objects.create(
            user=user,
            tenant=tenant,
            is_default=True
        )
        user.last_active_tenant = tenant
        user.save(update_fields=['last_active_tenant'])

        return user

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Tenant, TenantMembership


class TenantRequiredMixin(LoginRequiredMixin):
    """Mixin for class-based views that require a tenant context."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not getattr(request, 'tenant', None):
            tenant_slug = kwargs.get('tenant_slug')
            if tenant_slug:
                request.tenant = get_object_or_404(
                    Tenant, slug=tenant_slug, is_active=True
                )
            else:
                from django.shortcuts import redirect
                return redirect('tenants:select')
        return response

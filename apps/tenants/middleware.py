from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .managers import set_current_tenant
from .models import Tenant, TenantMembership


# Paths that don't require tenant context
TENANT_FREE_PATHS = [
    '/auth/',
    '/admin/',
    '/tenants/',
    '/__debug__/',
    '/static/',
    '/media/',
]


class TenantMiddleware:
    """
    Resolves the current tenant from:
    1. URL path: /t/{tenant_slug}/...
    2. Session: request.session['tenant_id']
    3. User's default tenant
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None

        # Skip for auth pages and static files
        if self._is_tenant_free(request.path):
            set_current_tenant(None)
            request.tenant = None
            response = self.get_response(request)
            set_current_tenant(None)
            return response

        # Root path redirect
        if request.path == '/':
            set_current_tenant(None)
            request.tenant = None
            response = self.get_response(request)
            set_current_tenant(None)
            return response

        try:
            # Strategy 1: URL path /t/{slug}/...
            tenant = self._resolve_from_url(request)

            # Strategy 2: Session
            if not tenant:
                tenant = self._resolve_from_session(request)

            # Strategy 3: User's default tenant
            if not tenant and request.user.is_authenticated:
                tenant = self._resolve_from_user(request)

            # Verify access
            if tenant and request.user.is_authenticated:
                if not request.user.is_superuser:
                    has_access = TenantMembership.objects.filter(
                        user=request.user, tenant=tenant
                    ).exists()
                    if not has_access:
                        raise PermissionDenied("You don't have access to this organization.")

            set_current_tenant(tenant)
            request.tenant = tenant
            if tenant:
                request.session['tenant_id'] = tenant.id

            response = self.get_response(request)
        finally:
            set_current_tenant(None)

        return response

    def _is_tenant_free(self, path):
        return any(path.startswith(prefix) for prefix in TENANT_FREE_PATHS)

    def _resolve_from_url(self, request):
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 't':
            try:
                return Tenant.objects.get(slug=path_parts[1], is_active=True)
            except Tenant.DoesNotExist:
                return None
        return None

    def _resolve_from_session(self, request):
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                return None
        return None

    def _resolve_from_user(self, request):
        membership = TenantMembership.objects.filter(
            user=request.user,
            tenant__is_active=True
        ).select_related('tenant').order_by('-is_default').first()
        if membership:
            return membership.tenant
        return None

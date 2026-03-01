from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from apps.roles.models import TenantUserRole
from apps.tenants.models import TenantMembership


def tenant_required(view_func):
    """Decorator that ensures a tenant context exists."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'tenant', None):
            return redirect('tenants:select')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*role_names):
    """Decorator that checks if the user has one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                return redirect('tenants:select')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            has_role = TenantUserRole.unscoped.filter(
                user=request.user,
                tenant=tenant,
                role__name__in=role_names
            ).exists()

            if not has_role:
                raise PermissionDenied("You don't have the required role.")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(*permission_codenames):
    """Decorator that checks if the user has one of the specified permissions."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                return redirect('tenants:select')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            has_perm = TenantUserRole.unscoped.filter(
                user=request.user,
                tenant=tenant,
                role__permissions__codename__in=permission_codenames
            ).exists()

            if not has_perm:
                raise PermissionDenied("You don't have the required permission.")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

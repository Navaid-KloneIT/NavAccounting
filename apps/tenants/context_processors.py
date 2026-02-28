from .models import TenantMembership


def tenant_context(request):
    """Inject tenant-related data into template context."""
    context = {
        'current_tenant': getattr(request, 'tenant', None),
        'user_tenants': [],
    }

    if hasattr(request, 'user') and request.user.is_authenticated:
        context['user_tenants'] = TenantMembership.objects.filter(
            user=request.user,
            tenant__is_active=True
        ).select_related('tenant').order_by('-is_default')

    return context

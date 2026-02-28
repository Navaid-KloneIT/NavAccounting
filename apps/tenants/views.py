from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .forms import TenantCreateForm
from .models import Tenant, TenantMembership


@login_required
def tenant_select(request):
    """Show tenant selection page or redirect if only one tenant."""
    memberships = TenantMembership.objects.filter(
        user=request.user,
        tenant__is_active=True
    ).select_related('tenant')

    if memberships.count() == 1:
        tenant = memberships.first().tenant
        request.session['tenant_id'] = tenant.id
        return redirect('dashboard:index', tenant_slug=tenant.slug)

    if memberships.count() == 0:
        return redirect('tenants:create')

    return render(request, 'tenants/select.html', {
        'memberships': memberships,
    })


@login_required
def tenant_create(request):
    """Create a new tenant/organization."""
    if request.method == 'POST':
        form = TenantCreateForm(request.POST)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.owner = request.user
            tenant.save()
            TenantMembership.objects.create(
                user=request.user,
                tenant=tenant,
                is_default=True
            )
            request.session['tenant_id'] = tenant.id
            return redirect('dashboard:index', tenant_slug=tenant.slug)
    else:
        form = TenantCreateForm()

    return render(request, 'tenants/create.html', {
        'form': form,
    })


@login_required
def tenant_switch(request, tenant_slug):
    """Switch to a different tenant."""
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)

    if not request.user.is_superuser:
        get_object_or_404(TenantMembership, user=request.user, tenant=tenant)

    request.session['tenant_id'] = tenant.id
    return redirect('dashboard:index', tenant_slug=tenant.slug)

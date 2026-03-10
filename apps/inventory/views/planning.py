from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import ReorderFilterForm
from ..models import ItemCategory, ReorderSuggestion


# =============================================================================
# Reorder Planning
# =============================================================================

@login_required
def reorder_dashboard(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ReorderSuggestion.objects.filter(tenant=tenant).select_related(
        'item', 'item__category', 'vendor'
    )

    filter_form = ReorderFilterForm(request.GET, tenant=tenant)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        if status:
            qs = qs.filter(status=status)
        category = filter_form.cleaned_data.get('category')
        if category:
            qs = qs.filter(item__category=category)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    stats = {
        'pending': ReorderSuggestion.objects.filter(tenant=tenant, status='pending').count(),
        'approved': ReorderSuggestion.objects.filter(tenant=tenant, status='approved').count(),
        'ordered': ReorderSuggestion.objects.filter(tenant=tenant, status='ordered').count(),
    }

    categories = ItemCategory.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'inventory/reorder/reorder_dashboard.html', {
        'suggestions': page_obj,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': qs.count(),
        'stats': stats,
        'categories': categories,
    })


@login_required
def reorder_generate(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        from ..services import generate_reorder_suggestions
        count = generate_reorder_suggestions(tenant)
        messages.success(request, f'{count} reorder suggestion(s) generated.')

    return redirect('inventory:reorder_dashboard', tenant_slug=tenant.slug)


@login_required
def reorder_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    suggestion = get_object_or_404(ReorderSuggestion.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and suggestion.status == 'pending':
        suggestion.status = 'approved'
        suggestion.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Reorder suggestion for {suggestion.item.sku} approved.')

    return redirect('inventory:reorder_dashboard', tenant_slug=tenant.slug)


@login_required
def reorder_dismiss(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    suggestion = get_object_or_404(ReorderSuggestion.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and suggestion.status == 'pending':
        suggestion.status = 'dismissed'
        suggestion.save(update_fields=['status', 'updated_at'])
        messages.info(request, f'Reorder suggestion for {suggestion.item.sku} dismissed.')

    return redirect('inventory:reorder_dashboard', tenant_slug=tenant.slug)


@login_required
def reorder_create_po(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    suggestion = get_object_or_404(ReorderSuggestion.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and suggestion.status == 'approved' and suggestion.vendor:
        from ..services import create_po_from_reorder
        po = create_po_from_reorder(suggestion, tenant, request.user)
        suggestion.status = 'ordered'
        suggestion.purchase_order = po
        suggestion.save(update_fields=['status', 'purchase_order', 'updated_at'])
        messages.success(request, f'Purchase Order {po.po_number} created.')
        return redirect('inventory:po_detail', tenant_slug=tenant.slug, pk=po.pk)

    messages.error(request, 'Cannot create PO. Ensure suggestion is approved and has a vendor.')
    return redirect('inventory:reorder_dashboard', tenant_slug=tenant.slug)

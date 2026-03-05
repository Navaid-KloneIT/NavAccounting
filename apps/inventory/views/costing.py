from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import COGSCalculationForm
from ..models import COGSCalculation, Item, ItemCategory, CostLayer


# =============================================================================
# COGS
# =============================================================================

@login_required
def cogs_dashboard(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    calculations = COGSCalculation.objects.filter(tenant=tenant).select_related(
        'period', 'created_by'
    ).order_by('-calculation_date')

    paginator = Paginator(calculations, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/cogs/cogs_dashboard.html', {
        'calculations': page_obj,
        'page_obj': page_obj,
        'total_count': calculations.count(),
    })


@login_required
def cogs_calculate(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = COGSCalculationForm(request.POST, tenant=tenant)
        if form.is_valid():
            calc = form.save(commit=False)
            calc.tenant = tenant
            calc.calculation_number = COGSCalculation.generate_calculation_number(tenant)
            calc.created_by = request.user
            calc.save()

            from ..services import run_cogs_calculation
            run_cogs_calculation(calc, tenant)

            messages.success(request, f'COGS Calculation {calc.calculation_number} completed.')
            return redirect('inventory:cogs_detail', tenant_slug=tenant.slug, pk=calc.pk)
    else:
        form = COGSCalculationForm(tenant=tenant, initial={
            'calculation_date': timezone.now().date()
        })

    return render(request, 'inventory/cogs/cogs_calculate.html', {
        'form': form,
    })


@login_required
def cogs_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    calc = get_object_or_404(
        COGSCalculation.unscoped.select_related('period', 'created_by', 'journal_entry'),
        pk=pk, tenant=tenant
    )
    entries = calc.entries.select_related('item')

    return render(request, 'inventory/cogs/cogs_detail.html', {
        'calculation': calc,
        'entries': entries,
    })


@login_required
def cogs_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    calc = get_object_or_404(COGSCalculation.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and calc.status == 'draft':
        from ..services import post_cogs_calculation
        post_cogs_calculation(calc, tenant, request.user)
        messages.success(request, f'COGS Calculation {calc.calculation_number} posted.')

    return redirect('inventory:cogs_detail', tenant_slug=tenant.slug, pk=pk)


# =============================================================================
# Valuation Report
# =============================================================================

@login_required
def valuation_report(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    items = Item.objects.filter(
        tenant=tenant, is_active=True, item_type='inventory'
    ).select_related('category', 'base_uom').order_by('category__code', 'sku')

    categories = ItemCategory.objects.filter(tenant=tenant, is_active=True)

    category_filter = request.GET.get('category', '')
    if category_filter:
        items = items.filter(category_id=category_filter)

    total_value = Decimal('0.00')
    item_data = []
    for item in items:
        value = item.inventory_value
        total_value += value
        item_data.append({
            'item': item,
            'value': value,
        })

    return render(request, 'inventory/valuation/valuation_report.html', {
        'item_data': item_data,
        'categories': categories,
        'total_value': total_value,
        'current_category': category_filter,
    })

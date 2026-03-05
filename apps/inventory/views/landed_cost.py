from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import LandedCostVoucherForm, LandedCostLineFormSet
from ..models import LandedCostVoucher, GoodsReceipt


# =============================================================================
# Landed Cost
# =============================================================================

@login_required
def landed_cost_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = LandedCostVoucher.objects.filter(tenant=tenant).select_related(
        'goods_receipt', 'created_by'
    )
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(voucher_number__icontains=search) |
            Q(goods_receipt__receipt_number__icontains=search)
        )

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/landed_cost/landed_cost_list.html', {
        'vouchers': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def landed_cost_create(request, tenant_slug, receipt_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    receipt = get_object_or_404(GoodsReceipt.unscoped, pk=receipt_pk, tenant=tenant)

    if request.method == 'POST':
        form = LandedCostVoucherForm(request.POST)
        formset = LandedCostLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            voucher = form.save(commit=False)
            voucher.tenant = tenant
            voucher.voucher_number = LandedCostVoucher.generate_voucher_number(tenant)
            voucher.goods_receipt = receipt
            voucher.created_by = request.user
            voucher.save()
            formset.instance = voucher
            formset.save()
            voucher.update_total()
            messages.success(request, f'Landed Cost Voucher {voucher.voucher_number} created.')
            return redirect('inventory:landed_cost_detail', tenant_slug=tenant.slug, pk=voucher.pk)
    else:
        form = LandedCostVoucherForm(initial={'date': timezone.now().date()})
        formset = LandedCostLineFormSet()

    return render(request, 'inventory/landed_cost/landed_cost_form.html', {
        'form': form, 'formset': formset, 'receipt': receipt,
    })


@login_required
def landed_cost_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    voucher = get_object_or_404(
        LandedCostVoucher.unscoped.select_related(
            'goods_receipt', 'created_by', 'journal_entry'
        ),
        pk=pk, tenant=tenant
    )
    cost_lines = voucher.cost_lines.all()
    allocations = voucher.allocations.select_related('item', 'goods_receipt_line')

    return render(request, 'inventory/landed_cost/landed_cost_detail.html', {
        'voucher': voucher,
        'cost_lines': cost_lines,
        'allocations': allocations,
    })


@login_required
def landed_cost_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    voucher = get_object_or_404(LandedCostVoucher.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and voucher.status == 'draft':
        from ..services import post_landed_cost
        post_landed_cost(voucher, tenant, request.user)
        messages.success(request, f'Landed Cost Voucher {voucher.voucher_number} posted.')

    return redirect('inventory:landed_cost_detail', tenant_slug=tenant.slug, pk=pk)

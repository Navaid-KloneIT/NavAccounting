from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import (
    InventoryAdjustmentForm, InventoryScrapForm, TransactionFilterForm,
    InventoryTransferForm, InventoryTransferLineFormSet,
)
from ..models import InventoryTransaction, InventoryTransfer, Item


# =============================================================================
# Inventory Transactions
# =============================================================================

@login_required
def transaction_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = InventoryTransaction.objects.filter(tenant=tenant).select_related('item', 'warehouse')

    filter_form = TransactionFilterForm(request.GET, tenant=tenant)
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(transaction_number__icontains=search) |
                Q(item__sku__icontains=search) |
                Q(item__name__icontains=search)
            )
        txn_type = filter_form.cleaned_data.get('transaction_type')
        if txn_type:
            qs = qs.filter(transaction_type=txn_type)
        item = filter_form.cleaned_data.get('item')
        if item:
            qs = qs.filter(item=item)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    items = Item.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'inventory/transactions/transaction_list.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': qs.count(),
        'transaction_type_choices': InventoryTransaction.TRANSACTION_TYPE_CHOICES,
        'items': items,
    })


@login_required
def transaction_adjustment(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = InventoryAdjustmentForm(request.POST, tenant=tenant)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.tenant = tenant
            txn.transaction_number = InventoryTransaction.generate_transaction_number(tenant)
            txn.transaction_type = 'adjustment'
            txn.posted_by = request.user
            txn.save()

            from ..services import process_inventory_transaction
            process_inventory_transaction(txn, tenant, request.user)

            messages.success(request, f'Adjustment {txn.transaction_number} recorded.')
            return redirect('inventory:transaction_list', tenant_slug=tenant.slug)
    else:
        form = InventoryAdjustmentForm(tenant=tenant, initial={'date': timezone.now().date()})

    return render(request, 'inventory/transactions/adjustment_form.html', {
        'form': form, 'transaction_type': 'Adjustment',
    })


@login_required
def transaction_scrap(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = InventoryScrapForm(request.POST, tenant=tenant)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.tenant = tenant
            txn.transaction_number = InventoryTransaction.generate_transaction_number(tenant)
            txn.transaction_type = 'scrap'
            txn.posted_by = request.user
            if txn.quantity > 0:
                txn.quantity = -txn.quantity
            txn.save()

            from ..services import process_inventory_transaction
            process_inventory_transaction(txn, tenant, request.user)

            messages.success(request, f'Scrap {txn.transaction_number} recorded.')
            return redirect('inventory:transaction_list', tenant_slug=tenant.slug)
    else:
        form = InventoryScrapForm(tenant=tenant, initial={'date': timezone.now().date()})

    return render(request, 'inventory/transactions/scrap_form.html', {
        'form': form, 'transaction_type': 'Scrap',
    })


# =============================================================================
# Inventory Transfers
# =============================================================================

@login_required
def transfer_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = InventoryTransfer.objects.filter(tenant=tenant).select_related(
        'from_warehouse', 'to_warehouse', 'created_by'
    )
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(transfer_number__icontains=search))

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/transfers/transfer_list.html', {
        'transfers': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': InventoryTransfer.STATUS_CHOICES,
        'current_status': status,
    })


@login_required
def transfer_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = InventoryTransferForm(request.POST, tenant=tenant)
        formset = InventoryTransferLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            transfer = form.save(commit=False)
            transfer.tenant = tenant
            transfer.transfer_number = InventoryTransfer.generate_transfer_number(tenant)
            transfer.created_by = request.user
            transfer.save()
            formset.instance = transfer
            formset.save()
            messages.success(request, f'Transfer {transfer.transfer_number} created.')
            return redirect('inventory:transfer_detail', tenant_slug=tenant.slug, pk=transfer.pk)
    else:
        form = InventoryTransferForm(tenant=tenant, initial={'date': timezone.now().date()})
        formset = InventoryTransferLineFormSet()

    return render(request, 'inventory/transfers/transfer_form.html', {
        'form': form, 'formset': formset,
    })


@login_required
def transfer_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    transfer = get_object_or_404(
        InventoryTransfer.unscoped.select_related(
            'from_warehouse', 'to_warehouse', 'created_by'
        ),
        pk=pk, tenant=tenant
    )
    lines = transfer.lines.select_related('item')

    return render(request, 'inventory/transfers/transfer_detail.html', {
        'transfer': transfer,
        'lines': lines,
    })


@login_required
def transfer_complete(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    transfer = get_object_or_404(InventoryTransfer.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and transfer.status in ('draft', 'in_transit'):
        from ..services import complete_inventory_transfer
        complete_inventory_transfer(transfer, tenant, request.user)
        messages.success(request, f'Transfer {transfer.transfer_number} completed.')

    return redirect('inventory:transfer_detail', tenant_slug=tenant.slug, pk=pk)

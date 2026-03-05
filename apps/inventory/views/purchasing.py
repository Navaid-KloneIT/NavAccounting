from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import (
    PurchaseRequisitionForm, PurchaseRequisitionLineFormSet,
    PurchaseOrderForm, PurchaseOrderLineFormSet,
    GoodsReceiptForm, GoodsReceiptLineFormSet,
)
from ..models import (
    PurchaseRequisition, PurchaseRequisitionLine,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine, Item,
)


# =============================================================================
# Purchase Requisitions
# =============================================================================

@login_required
def requisition_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = PurchaseRequisition.objects.filter(tenant=tenant).select_related('requested_by')
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(requisition_number__icontains=search))

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/requisitions/requisition_list.html', {
        'requisitions': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': PurchaseRequisition.STATUS_CHOICES,
        'current_status': status,
    })


@login_required
def requisition_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PurchaseRequisitionForm(request.POST)
        formset = PurchaseRequisitionLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            req = form.save(commit=False)
            req.tenant = tenant
            req.requisition_number = PurchaseRequisition.generate_requisition_number(tenant)
            req.requested_by = request.user
            req.save()
            formset.instance = req
            formset.save()
            messages.success(request, f'Requisition {req.requisition_number} created.')
            return redirect('inventory:requisition_detail', tenant_slug=tenant.slug, pk=req.pk)
    else:
        form = PurchaseRequisitionForm()
        formset = PurchaseRequisitionLineFormSet()

    return render(request, 'inventory/requisitions/requisition_form.html', {
        'form': form, 'formset': formset,
    })


@login_required
def requisition_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    req = get_object_or_404(
        PurchaseRequisition.unscoped.select_related('requested_by'),
        pk=pk, tenant=tenant
    )
    lines = req.lines.select_related('item', 'uom')

    return render(request, 'inventory/requisitions/requisition_detail.html', {
        'requisition': req,
        'lines': lines,
    })


@login_required
def requisition_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    req = get_object_or_404(PurchaseRequisition.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve' and req.status == 'submitted':
            req.status = 'approved'
            req.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Requisition {req.requisition_number} approved.')
        elif action == 'reject' and req.status == 'submitted':
            req.status = 'rejected'
            req.save(update_fields=['status', 'updated_at'])
            messages.warning(request, f'Requisition {req.requisition_number} rejected.')
        elif action == 'submit' and req.status == 'draft':
            req.status = 'submitted'
            req.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Requisition {req.requisition_number} submitted.')

    return redirect('inventory:requisition_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def requisition_convert(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    req = get_object_or_404(PurchaseRequisition.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and req.status == 'approved':
        po = PurchaseOrder(
            tenant=tenant,
            po_number=PurchaseOrder.generate_po_number(tenant),
            vendor_id=request.POST.get('vendor'),
            requisition=req,
            date=timezone.now().date(),
            created_by=request.user,
        )
        po.save()

        for line in req.lines.all():
            PurchaseOrderLine.objects.create(
                purchase_order=po,
                item=line.item,
                quantity=line.quantity,
                unit_price=line.estimated_unit_price,
                uom=line.uom,
            )

        po.update_total()
        req.status = 'converted'
        req.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Purchase Order {po.po_number} created from requisition.')
        return redirect('inventory:po_detail', tenant_slug=tenant.slug, pk=po.pk)

    return redirect('inventory:requisition_detail', tenant_slug=tenant.slug, pk=pk)


# =============================================================================
# Purchase Orders
# =============================================================================

@login_required
def po_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = PurchaseOrder.objects.filter(tenant=tenant).select_related('vendor', 'created_by')
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(po_number__icontains=search) | Q(vendor__name__icontains=search)
        )

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/purchase_orders/po_list.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'current_status': status,
    })


@login_required
def po_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, tenant=tenant)
        formset = PurchaseOrderLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            po = form.save(commit=False)
            po.tenant = tenant
            po.po_number = PurchaseOrder.generate_po_number(tenant)
            po.created_by = request.user
            po.save()
            formset.instance = po
            formset.save()
            po.update_total()
            messages.success(request, f'Purchase Order {po.po_number} created.')
            return redirect('inventory:po_detail', tenant_slug=tenant.slug, pk=po.pk)
    else:
        form = PurchaseOrderForm(tenant=tenant)
        formset = PurchaseOrderLineFormSet()

    return render(request, 'inventory/purchase_orders/po_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def po_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    po = get_object_or_404(
        PurchaseOrder.unscoped.select_related('vendor', 'created_by', 'approved_by', 'requisition'),
        pk=pk, tenant=tenant
    )
    lines = po.lines.select_related('item', 'uom')
    receipts = po.goods_receipts.all()

    return render(request, 'inventory/purchase_orders/po_detail.html', {
        'po': po,
        'lines': lines,
        'receipts': receipts,
    })


@login_required
def po_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    po = get_object_or_404(PurchaseOrder.unscoped, pk=pk, tenant=tenant)
    if po.status not in ('draft', 'submitted'):
        messages.error(request, 'Cannot edit this purchase order.')
        return redirect('inventory:po_detail', tenant_slug=tenant.slug, pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po, tenant=tenant)
        formset = PurchaseOrderLineFormSet(request.POST, instance=po)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            po.update_total()
            messages.success(request, f'Purchase Order {po.po_number} updated.')
            return redirect('inventory:po_detail', tenant_slug=tenant.slug, pk=po.pk)
    else:
        form = PurchaseOrderForm(instance=po, tenant=tenant)
        formset = PurchaseOrderLineFormSet(instance=po)

    return render(request, 'inventory/purchase_orders/po_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'po': po,
    })


@login_required
def po_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    po = get_object_or_404(PurchaseOrder.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve' and po.status in ('draft', 'submitted'):
            po.status = 'approved'
            po.approved_by = request.user
            po.save(update_fields=['status', 'approved_by', 'updated_at'])
            messages.success(request, f'Purchase Order {po.po_number} approved.')
        elif action == 'submit' and po.status == 'draft':
            po.status = 'submitted'
            po.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Purchase Order {po.po_number} submitted.')
        elif action == 'cancel' and po.status in ('draft', 'submitted', 'approved'):
            po.status = 'cancelled'
            po.save(update_fields=['status', 'updated_at'])
            messages.warning(request, f'Purchase Order {po.po_number} cancelled.')

    return redirect('inventory:po_detail', tenant_slug=tenant.slug, pk=pk)


# =============================================================================
# Goods Receipts
# =============================================================================

@login_required
def receipt_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = GoodsReceipt.objects.filter(tenant=tenant).select_related(
        'purchase_order', 'received_by', 'warehouse'
    )
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(receipt_number__icontains=search) |
            Q(purchase_order__po_number__icontains=search)
        )

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/goods_receipts/receipt_list.html', {
        'receipts': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def receipt_create(request, tenant_slug, po_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    po = get_object_or_404(PurchaseOrder.unscoped, pk=po_pk, tenant=tenant)
    if po.status not in ('approved', 'partially_received'):
        messages.error(request, 'Cannot create receipt for this purchase order.')
        return redirect('inventory:po_detail', tenant_slug=tenant.slug, pk=po_pk)

    if request.method == 'POST':
        form = GoodsReceiptForm(request.POST, tenant=tenant)
        formset = GoodsReceiptLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            receipt = form.save(commit=False)
            receipt.tenant = tenant
            receipt.receipt_number = GoodsReceipt.generate_receipt_number(tenant)
            receipt.purchase_order = po
            receipt.received_by = request.user
            receipt.save()
            formset.instance = receipt
            formset.save()
            messages.success(request, f'Goods Receipt {receipt.receipt_number} created.')
            return redirect('inventory:receipt_detail', tenant_slug=tenant.slug, pk=receipt.pk)
    else:
        form = GoodsReceiptForm(tenant=tenant, initial={'receipt_date': timezone.now().date()})
        formset = GoodsReceiptLineFormSet()

    return render(request, 'inventory/goods_receipts/receipt_form.html', {
        'form': form, 'formset': formset, 'po': po,
    })


@login_required
def receipt_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    receipt = get_object_or_404(
        GoodsReceipt.unscoped.select_related(
            'purchase_order', 'received_by', 'warehouse', 'journal_entry'
        ),
        pk=pk, tenant=tenant
    )
    lines = receipt.lines.select_related('item', 'po_line')

    return render(request, 'inventory/goods_receipts/receipt_detail.html', {
        'receipt': receipt,
        'lines': lines,
    })


@login_required
def receipt_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    receipt = get_object_or_404(GoodsReceipt.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and receipt.status == 'draft':
        from ..services import post_goods_receipt
        post_goods_receipt(receipt, tenant, request.user)
        messages.success(request, f'Goods Receipt {receipt.receipt_number} posted.')

    return redirect('inventory:receipt_detail', tenant_slug=tenant.slug, pk=pk)

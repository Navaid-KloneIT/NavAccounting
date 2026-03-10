from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import TransferPricingPolicyForm, TransferPricingTransactionForm
from ..models import Entity, TransferPricingPolicy, TransferPricingTransaction


@login_required
def tp_policy_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TransferPricingPolicy.objects.filter(tenant=tenant).select_related(
        'from_entity', 'to_entity'
    )

    total_count = qs.count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(policy_number__icontains=search) | Q(name__icontains=search))

    # Entity filter
    entity_id = request.GET.get('entity', '')
    if entity_id:
        qs = qs.filter(Q(from_entity_id=entity_id) | Q(to_entity_id=entity_id))

    # Method filter
    method = request.GET.get('method', '')
    if method:
        qs = qs.filter(pricing_method=method)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    entities = Entity.unscoped.filter(tenant=tenant, status='active')

    return render(request, 'multi_entity/transfer_pricing/tp_policy_list.html', {
        'policies': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'entities': entities,
        'method_choices': TransferPricingPolicy.PRICING_METHOD_CHOICES,
        'status_choices': TransferPricingPolicy.STATUS_CHOICES,
    })


@login_required
def tp_policy_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TransferPricingPolicyForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.policy_number = TransferPricingPolicy.generate_policy_number(tenant)
            obj.created_by = request.user
            obj.status = 'draft'
            obj.save()
            messages.success(request, f'Transfer pricing policy {obj.policy_number} created.')
            return redirect('multi_entity:tp_policy_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = TransferPricingPolicyForm(tenant=tenant)

    return render(request, 'multi_entity/transfer_pricing/tp_policy_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def tp_policy_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    policy = get_object_or_404(
        TransferPricingPolicy.unscoped.select_related('from_entity', 'to_entity', 'created_by'),
        pk=pk, tenant=tenant
    )
    transactions = policy.transactions.select_related('intercompany_transaction').all()[:20]

    return render(request, 'multi_entity/transfer_pricing/tp_policy_detail.html', {
        'policy': policy,
        'transactions': transactions,
    })


@login_required
def tp_policy_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    policy = get_object_or_404(TransferPricingPolicy.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TransferPricingPolicyForm(request.POST, instance=policy, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Policy {policy.policy_number} updated.')
            return redirect('multi_entity:tp_policy_detail', tenant_slug=tenant.slug, pk=policy.pk)
    else:
        form = TransferPricingPolicyForm(instance=policy, tenant=tenant)

    return render(request, 'multi_entity/transfer_pricing/tp_policy_form.html', {
        'form': form,
        'policy': policy,
        'is_edit': True,
    })


@login_required
def tp_transaction_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TransferPricingTransaction.objects.filter(tenant=tenant).select_related(
        'policy', 'intercompany_transaction'
    )

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'multi_entity/transfer_pricing/tp_transaction_list.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
        'status_choices': TransferPricingTransaction.STATUS_CHOICES,
    })


@login_required
def tp_transaction_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TransferPricingTransactionForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, 'Transfer pricing transaction created.')
            return redirect('multi_entity:tp_transaction_list', tenant_slug=tenant.slug)
    else:
        form = TransferPricingTransactionForm(tenant=tenant)

    return render(request, 'multi_entity/transfer_pricing/tp_transaction_form.html', {
        'form': form,
    })


@login_required
def tp_transaction_review(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    txn = get_object_or_404(TransferPricingTransaction.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'approve' and txn.status in ('draft', 'reviewed'):
            txn.status = 'approved'
            txn.reviewed_by = request.user
            txn.reviewed_at = timezone.now()
            txn.save()
            messages.success(request, 'TP transaction approved.')
        elif action == 'flag' and txn.status in ('draft', 'reviewed'):
            txn.status = 'flagged'
            txn.reviewed_by = request.user
            txn.reviewed_at = timezone.now()
            txn.review_notes = request.POST.get('review_notes', '')
            txn.save()
            messages.warning(request, 'TP transaction flagged for review.')

    return redirect('multi_entity:tp_transaction_list', tenant_slug=tenant.slug)

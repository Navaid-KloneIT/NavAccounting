from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import IntercompanyTransactionForm
from ..models import Entity, IntercompanyBalance, IntercompanyTransaction


@login_required
def ic_transaction_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = IntercompanyTransaction.objects.filter(tenant=tenant).select_related(
        'from_entity', 'to_entity', 'currency', 'fiscal_period'
    )

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    posted_count = qs.filter(status='posted').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(transaction_number__icontains=search) | Q(description__icontains=search)
        )

    # Entity filter
    entity_id = request.GET.get('entity', '')
    if entity_id:
        qs = qs.filter(Q(from_entity_id=entity_id) | Q(to_entity_id=entity_id))

    # Type filter
    txn_type = request.GET.get('type', '')
    if txn_type:
        qs = qs.filter(transaction_type=txn_type)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    entities = Entity.unscoped.filter(tenant=tenant, status='active')

    return render(request, 'multi_entity/intercompany/ic_transaction_list.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'posted_count': posted_count,
        'entities': entities,
        'type_choices': IntercompanyTransaction.TRANSACTION_TYPE_CHOICES,
        'status_choices': IntercompanyTransaction.STATUS_CHOICES,
    })


@login_required
def ic_transaction_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = IntercompanyTransactionForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.transaction_number = IntercompanyTransaction.generate_transaction_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'IC Transaction {obj.transaction_number} created.')
            return redirect('multi_entity:ic_transaction_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = IntercompanyTransactionForm(tenant=tenant)

    return render(request, 'multi_entity/intercompany/ic_transaction_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def ic_transaction_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    txn = get_object_or_404(
        IntercompanyTransaction.unscoped.select_related(
            'from_entity', 'to_entity', 'currency', 'fiscal_period',
            'from_journal_entry', 'to_journal_entry', 'created_by', 'confirmed_by'
        ),
        pk=pk, tenant=tenant
    )

    return render(request, 'multi_entity/intercompany/ic_transaction_detail.html', {
        'txn': txn,
    })


@login_required
def ic_transaction_confirm(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    txn = get_object_or_404(IntercompanyTransaction.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and txn.status in ('draft', 'pending'):
        txn.status = 'confirmed'
        txn.confirmed_by = request.user
        txn.confirmed_at = timezone.now()
        txn.save()
        messages.success(request, f'IC Transaction {txn.transaction_number} confirmed.')

    return redirect('multi_entity:ic_transaction_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def ic_transaction_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    txn = get_object_or_404(IntercompanyTransaction.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and txn.status == 'confirmed':
        from ..services import post_ic_transaction
        try:
            post_ic_transaction(txn, tenant, request.user)
            messages.success(request, f'IC Transaction {txn.transaction_number} posted.')
        except Exception as e:
            messages.error(request, f'Error posting transaction: {e}')

    return redirect('multi_entity:ic_transaction_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def ic_balance_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = IntercompanyBalance.objects.filter(tenant=tenant).select_related(
        'from_entity', 'to_entity', 'fiscal_period', 'currency'
    )

    # Entity filter
    entity_id = request.GET.get('entity', '')
    if entity_id:
        qs = qs.filter(Q(from_entity_id=entity_id) | Q(to_entity_id=entity_id))

    # Reconciled filter
    reconciled = request.GET.get('reconciled', '')
    if reconciled == 'yes':
        qs = qs.filter(is_reconciled=True)
    elif reconciled == 'no':
        qs = qs.filter(is_reconciled=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    entities = Entity.unscoped.filter(tenant=tenant, status='active')

    return render(request, 'multi_entity/intercompany/ic_balance_list.html', {
        'balances': page_obj,
        'page_obj': page_obj,
        'entities': entities,
    })


@login_required
def ic_balance_reconcile(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    balance = get_object_or_404(IntercompanyBalance.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and not balance.is_reconciled:
        balance.is_reconciled = True
        balance.last_reconciled_at = timezone.now()
        balance.save()
        messages.success(request, 'IC Balance marked as reconciled.')

    return redirect('multi_entity:ic_balance_list', tenant_slug=tenant.slug)

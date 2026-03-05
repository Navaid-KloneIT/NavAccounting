from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import (
    CycleCountPlanForm, CycleCountSessionForm, CycleCountItemFormSet,
)
from ..models import CycleCountPlan, CycleCountSession, CycleCountItem, Item


# =============================================================================
# Cycle Count Plans
# =============================================================================

@login_required
def cycle_count_plan_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = CycleCountPlan.objects.filter(tenant=tenant).select_related('warehouse', 'category')
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(plan_number__icontains=search) | Q(name__icontains=search))

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/cycle_counts/plan_list.html', {
        'plans': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def cycle_count_plan_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CycleCountPlanForm(request.POST, tenant=tenant)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.tenant = tenant
            plan.plan_number = CycleCountPlan.generate_plan_number(tenant)
            plan.save()
            messages.success(request, f'Cycle Count Plan {plan.plan_number} created.')
            return redirect('inventory:cycle_count_plan_list', tenant_slug=tenant.slug)
    else:
        form = CycleCountPlanForm(tenant=tenant, initial={
            'next_count_date': timezone.now().date()
        })

    return render(request, 'inventory/cycle_counts/plan_form.html', {
        'form': form,
    })


# =============================================================================
# Cycle Count Sessions
# =============================================================================

@login_required
def cycle_count_session_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = CycleCountSession.objects.filter(tenant=tenant).select_related(
        'plan', 'counted_by', 'warehouse'
    )
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(session_number__icontains=search))

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/cycle_counts/session_list.html', {
        'sessions': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': CycleCountSession.STATUS_CHOICES,
        'current_status': status,
    })


@login_required
def cycle_count_session_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CycleCountSessionForm(request.POST, tenant=tenant)
        if form.is_valid():
            session = form.save(commit=False)
            session.tenant = tenant
            session.session_number = CycleCountSession.generate_session_number(tenant)
            session.counted_by = request.user
            session.save()

            # Auto-populate items based on warehouse/plan
            items_qs = Item.objects.filter(
                tenant=tenant, is_active=True, item_type='inventory'
            )
            if session.warehouse:
                pass  # Future: filter by warehouse stock
            if session.plan and session.plan.category:
                items_qs = items_qs.filter(category=session.plan.category)

            for item in items_qs:
                CycleCountItem.objects.create(
                    session=session,
                    item=item,
                    system_quantity=item.quantity_on_hand,
                )

            messages.success(request, f'Cycle Count Session {session.session_number} created with {items_qs.count()} items.')
            return redirect('inventory:cycle_count_session_detail', tenant_slug=tenant.slug, pk=session.pk)
    else:
        form = CycleCountSessionForm(tenant=tenant, initial={
            'count_date': timezone.now().date()
        })

    return render(request, 'inventory/cycle_counts/session_form.html', {
        'form': form,
    })


@login_required
def cycle_count_session_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    session = get_object_or_404(
        CycleCountSession.unscoped.select_related('plan', 'counted_by', 'warehouse'),
        pk=pk, tenant=tenant
    )
    items = session.items.select_related('item').order_by('item__sku')

    return render(request, 'inventory/cycle_counts/session_detail.html', {
        'session': session,
        'items': items,
    })


@login_required
def cycle_count_enter(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    session = get_object_or_404(CycleCountSession.unscoped, pk=pk, tenant=tenant)
    if session.status not in ('planned', 'in_progress'):
        messages.error(request, 'This session cannot be edited.')
        return redirect('inventory:cycle_count_session_detail', tenant_slug=tenant.slug, pk=pk)

    if request.method == 'POST':
        formset = CycleCountItemFormSet(request.POST, instance=session)
        if formset.is_valid():
            formset.save()
            session.status = 'in_progress'
            session.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Count entries saved.')
            return redirect('inventory:cycle_count_session_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        formset = CycleCountItemFormSet(instance=session)

    items = session.items.select_related('item').order_by('item__sku')

    return render(request, 'inventory/cycle_counts/count_form.html', {
        'session': session,
        'formset': formset,
        'items': items,
    })


@login_required
def cycle_count_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    session = get_object_or_404(CycleCountSession.unscoped, pk=pk, tenant=tenant)
    if request.method == 'POST' and session.status in ('in_progress', 'completed'):
        action = request.POST.get('action')
        if action == 'complete' and session.status == 'in_progress':
            session.status = 'completed'
            session.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Session {session.session_number} marked as completed.')
        elif action == 'approve' and session.status == 'completed':
            from ..services import approve_cycle_count
            approve_cycle_count(session, tenant, request.user)
            messages.success(request, f'Session {session.session_number} approved. Adjustments posted.')

    return redirect('inventory:cycle_count_session_detail', tenant_slug=tenant.slug, pk=pk)

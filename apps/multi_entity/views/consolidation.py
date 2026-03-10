from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import ConsolidationGroupForm, ConsolidationRunForm, EliminationRuleForm
from ..models import (
    ConsolidationGroup,
    ConsolidationRun,
    EliminationRule,
    Entity,
)


# =============================================================================
# Consolidation Groups
# =============================================================================

@login_required
def consolidation_group_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ConsolidationGroup.objects.filter(tenant=tenant).select_related(
        'parent_entity', 'reporting_currency'
    )

    total_count = qs.count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search))

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'multi_entity/consolidation/consolidation_group_list.html', {
        'groups': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
    })


@login_required
def consolidation_group_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ConsolidationGroupForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            form.save_m2m()
            messages.success(request, f'Consolidation group "{obj.code}" created.')
            return redirect('multi_entity:consolidation_group_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = ConsolidationGroupForm(tenant=tenant)

    return render(request, 'multi_entity/consolidation/consolidation_group_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def consolidation_group_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    group = get_object_or_404(
        ConsolidationGroup.unscoped.select_related('parent_entity', 'reporting_currency'),
        pk=pk, tenant=tenant
    )
    member_entities = group.entities.all()
    elimination_rules = group.elimination_rules.all()
    recent_runs = group.runs.all()[:10]

    return render(request, 'multi_entity/consolidation/consolidation_group_detail.html', {
        'group': group,
        'member_entities': member_entities,
        'elimination_rules': elimination_rules,
        'recent_runs': recent_runs,
    })


@login_required
def consolidation_group_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    group = get_object_or_404(ConsolidationGroup.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ConsolidationGroupForm(request.POST, instance=group, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Consolidation group "{group.code}" updated.')
            return redirect('multi_entity:consolidation_group_detail', tenant_slug=tenant.slug, pk=group.pk)
    else:
        form = ConsolidationGroupForm(instance=group, tenant=tenant)

    return render(request, 'multi_entity/consolidation/consolidation_group_form.html', {
        'form': form,
        'group': group,
        'is_edit': True,
    })


# =============================================================================
# Elimination Rules
# =============================================================================

@login_required
def elimination_rule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = EliminationRule.objects.filter(tenant=tenant).select_related(
        'consolidation_group', 'debit_account', 'credit_account'
    )

    total_count = qs.count()

    # Group filter
    group_id = request.GET.get('group', '')
    if group_id:
        qs = qs.filter(consolidation_group_id=group_id)

    # Rule type filter
    rule_type = request.GET.get('rule_type', '')
    if rule_type:
        qs = qs.filter(rule_type=rule_type)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    groups = ConsolidationGroup.unscoped.filter(tenant=tenant, is_active=True)

    return render(request, 'multi_entity/consolidation/elimination_rule_list.html', {
        'rules': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'groups': groups,
        'rule_type_choices': EliminationRule.RULE_TYPE_CHOICES,
    })


@login_required
def elimination_rule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = EliminationRuleForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Elimination rule "{obj.name}" created.')
            return redirect('multi_entity:elimination_rule_list', tenant_slug=tenant.slug)
    else:
        form = EliminationRuleForm(tenant=tenant)

    return render(request, 'multi_entity/consolidation/elimination_rule_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def elimination_rule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(EliminationRule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = EliminationRuleForm(request.POST, instance=rule, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Elimination rule "{rule.name}" updated.')
            return redirect('multi_entity:elimination_rule_list', tenant_slug=tenant.slug)
    else:
        form = EliminationRuleForm(instance=rule, tenant=tenant)

    return render(request, 'multi_entity/consolidation/elimination_rule_form.html', {
        'form': form,
        'rule': rule,
        'is_edit': True,
    })


# =============================================================================
# Consolidation Runs
# =============================================================================

@login_required
def consolidation_run_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ConsolidationRun.objects.filter(tenant=tenant).select_related(
        'consolidation_group', 'fiscal_period', 'created_by'
    )

    total_count = qs.count()

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    # Group filter
    group_id = request.GET.get('group', '')
    if group_id:
        qs = qs.filter(consolidation_group_id=group_id)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    groups = ConsolidationGroup.unscoped.filter(tenant=tenant, is_active=True)

    return render(request, 'multi_entity/consolidation/consolidation_run_list.html', {
        'runs': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'groups': groups,
        'status_choices': ConsolidationRun.STATUS_CHOICES,
    })


@login_required
def consolidation_run_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ConsolidationRunForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.run_number = ConsolidationRun.generate_run_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Consolidation run {obj.run_number} created.')
            return redirect('multi_entity:consolidation_run_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = ConsolidationRunForm(tenant=tenant)

    return render(request, 'multi_entity/consolidation/consolidation_run_form.html', {
        'form': form,
    })


@login_required
def consolidation_run_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    run = get_object_or_404(
        ConsolidationRun.unscoped.select_related(
            'consolidation_group', 'fiscal_period', 'created_by'
        ),
        pk=pk, tenant=tenant
    )
    elimination_entries = run.elimination_entries.select_related(
        'from_entity', 'to_entity', 'debit_account', 'credit_account'
    ).all()
    minority_interests = run.minority_interests.select_related('entity', 'fiscal_period').all()

    return render(request, 'multi_entity/consolidation/consolidation_run_detail.html', {
        'run': run,
        'elimination_entries': elimination_entries,
        'minority_interests': minority_interests,
    })


@login_required
def consolidation_run_execute(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    run = get_object_or_404(ConsolidationRun.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and run.status == 'draft':
        from ..services import execute_consolidation
        try:
            execute_consolidation(run, tenant, request.user)
            messages.success(request, f'Consolidation run {run.run_number} executed successfully.')
        except Exception as e:
            messages.error(request, f'Consolidation error: {e}')

    return redirect('multi_entity:consolidation_run_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def consolidation_run_reverse(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    run = get_object_or_404(ConsolidationRun.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and run.status == 'completed':
        from ..services import reverse_consolidation
        try:
            reverse_consolidation(run, tenant, request.user)
            messages.success(request, f'Consolidation run {run.run_number} reversed.')
        except Exception as e:
            messages.error(request, f'Reversal error: {e}')

    return redirect('multi_entity:consolidation_run_detail', tenant_slug=tenant.slug, pk=pk)

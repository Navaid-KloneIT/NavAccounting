from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import ProjectForm, WBSElementForm, ProjectBudgetForm, BillingRuleForm
from ..models import Project, WBSElement, ProjectBudget, BillingRule


# -------------------------------------------------------------------------
# Project CRUD
# -------------------------------------------------------------------------

@login_required
def project_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Project.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(project_number__icontains=search) |
            Q(name__icontains=search) |
            Q(client_name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    billing_filter = request.GET.get('billing_type', '')
    if billing_filter:
        qs = qs.filter(billing_type=billing_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'project_costing/projects/project_list.html', {
        'projects': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def project_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ProjectForm(request.POST, tenant=tenant)
        if form.is_valid():
            project = form.save(commit=False)
            project.tenant = tenant
            project.project_number = Project.generate_project_number(tenant)
            project.save()
            messages.success(request, f'Project "{project.name}" created.')
            return redirect('project_costing:project_detail', tenant_slug=tenant.slug, pk=project.pk)
    else:
        form = ProjectForm(tenant=tenant)

    return render(request, 'project_costing/projects/project_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def project_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=pk, tenant=tenant)
    wbs_elements = project.wbs_elements.all()
    budgets = project.budgets.select_related('gl_account', 'wbs_element').all()
    billing_rules = project.billing_rules.all()
    milestones = project.milestones.all()
    recent_time = project.time_entries.select_related('employee').order_by('-entry_date')[:10]
    recent_expenses = project.expense_entries.order_by('-entry_date')[:10]

    budget_totals = budgets.aggregate(
        total_budget=Sum('budget_amount'),
        total_revised=Sum('revised_amount'),
    )
    time_totals = project.time_entries.aggregate(
        total_hours=Sum('hours'),
        total_amount=Sum('total_amount'),
    )
    expense_totals = project.expense_entries.aggregate(
        total_amount=Sum('amount'),
    )

    return render(request, 'project_costing/projects/project_detail.html', {
        'project': project,
        'wbs_elements': wbs_elements,
        'budgets': budgets,
        'billing_rules': billing_rules,
        'milestones': milestones,
        'recent_time': recent_time,
        'recent_expenses': recent_expenses,
        'budget_totals': budget_totals,
        'time_totals': time_totals,
        'expense_totals': expense_totals,
    })


@login_required
def project_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" updated.')
            return redirect('project_costing:project_detail', tenant_slug=tenant.slug, pk=project.pk)
    else:
        form = ProjectForm(instance=project, tenant=tenant)

    return render(request, 'project_costing/projects/project_form.html', {
        'form': form, 'is_edit': True, 'project': project,
    })


# -------------------------------------------------------------------------
# WBS Element CRUD
# -------------------------------------------------------------------------

@login_required
def wbs_list(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    wbs_elements = WBSElement.unscoped.filter(project=project).select_related('parent')

    return render(request, 'project_costing/wbs/wbs_list.html', {
        'project': project,
        'wbs_elements': wbs_elements,
    })


@login_required
def wbs_create(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)

    if request.method == 'POST':
        form = WBSElementForm(request.POST, project=project)
        if form.is_valid():
            wbs = form.save(commit=False)
            wbs.tenant = tenant
            wbs.project = project
            if wbs.parent:
                wbs.level = wbs.parent.level + 1
            wbs.save()
            messages.success(request, f'WBS element "{wbs.code}" created.')
            return redirect('project_costing:wbs_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = WBSElementForm(project=project)

    return render(request, 'project_costing/wbs/wbs_form.html', {
        'form': form, 'project': project, 'is_edit': False,
    })


@login_required
def wbs_edit(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    wbs = get_object_or_404(WBSElement.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        form = WBSElementForm(request.POST, instance=wbs, project=project)
        if form.is_valid():
            wbs = form.save(commit=False)
            if wbs.parent:
                wbs.level = wbs.parent.level + 1
            wbs.save()
            messages.success(request, f'WBS element "{wbs.code}" updated.')
            return redirect('project_costing:wbs_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = WBSElementForm(instance=wbs, project=project)

    return render(request, 'project_costing/wbs/wbs_form.html', {
        'form': form, 'project': project, 'is_edit': True, 'wbs': wbs,
    })


@login_required
def wbs_delete(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    wbs = get_object_or_404(WBSElement.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        wbs.delete()
        messages.success(request, 'WBS element deleted.')
        return redirect('project_costing:wbs_list', tenant_slug=tenant.slug, project_pk=project.pk)

    return render(request, 'project_costing/wbs/wbs_confirm_delete.html', {
        'project': project, 'object': wbs,
    })


# -------------------------------------------------------------------------
# Budget CRUD
# -------------------------------------------------------------------------

@login_required
def budget_list(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    budgets = ProjectBudget.unscoped.filter(project=project).select_related(
        'gl_account', 'wbs_element', 'fiscal_period'
    )
    totals = budgets.aggregate(
        total_budget=Sum('budget_amount'),
        total_revised=Sum('revised_amount'),
    )

    return render(request, 'project_costing/budgets/budget_list.html', {
        'project': project,
        'budgets': budgets,
        'totals': totals,
    })


@login_required
def budget_create(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)

    if request.method == 'POST':
        form = ProjectBudgetForm(request.POST, tenant=tenant, project=project)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.tenant = tenant
            budget.project = project
            budget.save()
            messages.success(request, 'Budget line created.')
            return redirect('project_costing:budget_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = ProjectBudgetForm(tenant=tenant, project=project)

    return render(request, 'project_costing/budgets/budget_form.html', {
        'form': form, 'project': project, 'is_edit': False,
    })


@login_required
def budget_edit(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    budget = get_object_or_404(ProjectBudget.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        form = ProjectBudgetForm(request.POST, instance=budget, tenant=tenant, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget line updated.')
            return redirect('project_costing:budget_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = ProjectBudgetForm(instance=budget, tenant=tenant, project=project)

    return render(request, 'project_costing/budgets/budget_form.html', {
        'form': form, 'project': project, 'is_edit': True, 'budget': budget,
    })


@login_required
def budget_delete(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    budget = get_object_or_404(ProjectBudget.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget line deleted.')
        return redirect('project_costing:budget_list', tenant_slug=tenant.slug, project_pk=project.pk)

    return render(request, 'project_costing/budgets/budget_confirm_delete.html', {
        'project': project, 'object': budget,
    })


# -------------------------------------------------------------------------
# Billing Rule CRUD
# -------------------------------------------------------------------------

@login_required
def billing_rule_list(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    billing_rules = BillingRule.unscoped.filter(project=project)

    return render(request, 'project_costing/billing_rules/billing_rule_list.html', {
        'project': project,
        'billing_rules': billing_rules,
    })


@login_required
def billing_rule_create(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)

    if request.method == 'POST':
        form = BillingRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.tenant = tenant
            rule.project = project
            rule.save()
            messages.success(request, 'Billing rule created.')
            return redirect('project_costing:billing_rule_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = BillingRuleForm()

    return render(request, 'project_costing/billing_rules/billing_rule_form.html', {
        'form': form, 'project': project, 'is_edit': False,
    })


@login_required
def billing_rule_edit(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    rule = get_object_or_404(BillingRule.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        form = BillingRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Billing rule updated.')
            return redirect('project_costing:billing_rule_list', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = BillingRuleForm(instance=rule)

    return render(request, 'project_costing/billing_rules/billing_rule_form.html', {
        'form': form, 'project': project, 'is_edit': True, 'rule': rule,
    })


@login_required
def billing_rule_delete(request, tenant_slug, project_pk, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)
    rule = get_object_or_404(BillingRule.unscoped, pk=pk, project=project)

    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'Billing rule deleted.')
        return redirect('project_costing:billing_rule_list', tenant_slug=tenant.slug, project_pk=project.pk)

    return render(request, 'project_costing/billing_rules/billing_rule_confirm_delete.html', {
        'project': project, 'object': rule,
    })

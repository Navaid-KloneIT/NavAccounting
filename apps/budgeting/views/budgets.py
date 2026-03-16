from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant
from ..forms import BudgetForm, BudgetLineItemFormSet
from ..models import Budget
from ..services import recalculate_budget_total


@login_required
def budget_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Budget.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(budget_number__icontains=search) |
            Q(name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    budget_type_filter = request.GET.get('budget_type', '')
    if budget_type_filter:
        qs = qs.filter(budget_type=budget_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'budgeting/budgets/budget_list.html', {
        'budgets': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': Budget.STATUS_CHOICES,
        'budget_type_choices': Budget.BUDGET_TYPE_CHOICES,
    })


@login_required
def budget_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BudgetForm(request.POST, tenant=tenant)
        formset = BudgetLineItemFormSet(request.POST, prefix='lines', form_kwargs={'tenant': tenant})
        if form.is_valid() and formset.is_valid():
            budget = form.save(commit=False)
            budget.tenant = tenant
            budget.budget_number = Budget.generate_budget_number(tenant)
            budget.created_by = request.user
            budget.save()
            formset.instance = budget
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = tenant
                line.save()
            for obj in formset.deleted_objects:
                obj.delete()
            recalculate_budget_total(budget)
            messages.success(request, f'Budget "{budget.name}" created.')
            return redirect('budgeting:budget_detail', tenant_slug=tenant.slug, pk=budget.pk)
    else:
        form = BudgetForm(tenant=tenant)
        formset = BudgetLineItemFormSet(prefix='lines', form_kwargs={'tenant': tenant})

    return render(request, 'budgeting/budgets/budget_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def budget_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    budget = get_object_or_404(Budget.unscoped, pk=pk, tenant=tenant)
    line_items = budget.line_items.select_related('gl_account', 'fiscal_period').all()

    return render(request, 'budgeting/budgets/budget_detail.html', {
        'budget': budget,
        'line_items': line_items,
        'versions': budget.versions.all()[:5],
    })


@login_required
def budget_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    budget = get_object_or_404(Budget.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, tenant=tenant)
        formset = BudgetLineItemFormSet(
            request.POST, instance=budget, prefix='lines',
            form_kwargs={'tenant': tenant},
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = tenant
                line.save()
            for obj in formset.deleted_objects:
                obj.delete()
            recalculate_budget_total(budget)
            messages.success(request, f'Budget "{budget.name}" updated.')
            return redirect('budgeting:budget_detail', tenant_slug=tenant.slug, pk=budget.pk)
    else:
        form = BudgetForm(instance=budget, tenant=tenant)
        formset = BudgetLineItemFormSet(
            instance=budget, prefix='lines',
            form_kwargs={'tenant': tenant},
        )

    return render(request, 'budgeting/budgets/budget_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'budget': budget,
    })


@login_required
def budget_submit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    budget = get_object_or_404(Budget.unscoped, pk=pk, tenant=tenant)
    if budget.status == 'draft':
        budget.status = 'in_review'
        budget.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Budget "{budget.name}" submitted for review.')
    else:
        messages.warning(request, 'Budget can only be submitted from draft status.')
    return redirect('budgeting:budget_detail', tenant_slug=tenant.slug, pk=budget.pk)


@login_required
def budget_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    budget = get_object_or_404(Budget.unscoped, pk=pk, tenant=tenant)
    if budget.status == 'in_review':
        budget.status = 'approved'
        budget.approved_by = request.user
        budget.approved_at = timezone.now()
        budget.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        messages.success(request, f'Budget "{budget.name}" approved.')
    else:
        messages.warning(request, 'Budget can only be approved from in-review status.')
    return redirect('budgeting:budget_detail', tenant_slug=tenant.slug, pk=budget.pk)

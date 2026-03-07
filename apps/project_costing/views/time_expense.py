from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import TimeEntryForm, ExpenseEntryForm
from ..models import Project, TimeEntry, ExpenseEntry


# -------------------------------------------------------------------------
# Time Entry CRUD
# -------------------------------------------------------------------------

@login_required
def time_entry_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TimeEntry.objects.filter(tenant=tenant).select_related('project', 'employee', 'wbs_element')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search) |
            Q(project__project_number__icontains=search) |
            Q(description__icontains=search)
        )

    project_filter = request.GET.get('project', '')
    if project_filter:
        qs = qs.filter(project_id=project_filter)

    status_filter = request.GET.get('billing_status', '')
    if status_filter:
        qs = qs.filter(billing_status=status_filter)

    projects = Project.objects.filter(tenant=tenant, is_active=True)

    totals = qs.aggregate(total_hours=Sum('hours'), total_amount=Sum('total_amount'))

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'project_costing/time_entries/time_entry_list.html', {
        'time_entries': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'projects': projects,
        'totals': totals,
    })


@login_required
def time_entry_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TimeEntryForm(request.POST, tenant=tenant)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.tenant = tenant
            entry.save()
            messages.success(request, 'Time entry created.')
            return redirect('project_costing:time_entry_list', tenant_slug=tenant.slug)
    else:
        form = TimeEntryForm(tenant=tenant)

    return render(request, 'project_costing/time_entries/time_entry_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def time_entry_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    entry = get_object_or_404(TimeEntry.unscoped, pk=pk, tenant=tenant)

    if entry.billing_status == 'billed':
        messages.error(request, 'Cannot edit a billed time entry.')
        return redirect('project_costing:time_entry_list', tenant_slug=tenant.slug)

    if request.method == 'POST':
        form = TimeEntryForm(request.POST, instance=entry, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Time entry updated.')
            return redirect('project_costing:time_entry_list', tenant_slug=tenant.slug)
    else:
        form = TimeEntryForm(instance=entry, tenant=tenant)

    return render(request, 'project_costing/time_entries/time_entry_form.html', {
        'form': form, 'is_edit': True, 'entry': entry,
    })


@login_required
def time_entry_delete(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    entry = get_object_or_404(TimeEntry.unscoped, pk=pk, tenant=tenant)

    if entry.billing_status == 'billed':
        messages.error(request, 'Cannot delete a billed time entry.')
        return redirect('project_costing:time_entry_list', tenant_slug=tenant.slug)

    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Time entry deleted.')
        return redirect('project_costing:time_entry_list', tenant_slug=tenant.slug)

    return render(request, 'project_costing/time_entries/time_entry_confirm_delete.html', {
        'object': entry,
    })


@login_required
def time_entry_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    entry = get_object_or_404(TimeEntry.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        entry.approved_by = request.user
        entry.approved_date = timezone.now().date()
        entry.save()
        messages.success(request, 'Time entry approved.')

    return redirect('project_costing:time_entry_list', tenant_slug=tenant.slug)


# -------------------------------------------------------------------------
# Expense Entry CRUD
# -------------------------------------------------------------------------

@login_required
def expense_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ExpenseEntry.objects.filter(tenant=tenant).select_related('project', 'gl_account', 'wbs_element')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(description__icontains=search) |
            Q(vendor_name__icontains=search) |
            Q(project__project_number__icontains=search)
        )

    project_filter = request.GET.get('project', '')
    if project_filter:
        qs = qs.filter(project_id=project_filter)

    status_filter = request.GET.get('billing_status', '')
    if status_filter:
        qs = qs.filter(billing_status=status_filter)

    projects = Project.objects.filter(tenant=tenant, is_active=True)
    totals = qs.aggregate(total_amount=Sum('amount'), total_billed=Sum('billed_amount'))

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'project_costing/expenses/expense_list.html', {
        'expenses': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'projects': projects,
        'totals': totals,
    })


@login_required
def expense_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ExpenseEntryForm(request.POST, tenant=tenant)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.tenant = tenant
            expense.save()
            messages.success(request, 'Expense entry created.')
            return redirect('project_costing:expense_list', tenant_slug=tenant.slug)
    else:
        form = ExpenseEntryForm(tenant=tenant)

    return render(request, 'project_costing/expenses/expense_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def expense_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    expense = get_object_or_404(ExpenseEntry.unscoped, pk=pk, tenant=tenant)

    if expense.billing_status == 'billed':
        messages.error(request, 'Cannot edit a billed expense.')
        return redirect('project_costing:expense_list', tenant_slug=tenant.slug)

    if request.method == 'POST':
        form = ExpenseEntryForm(request.POST, instance=expense, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense entry updated.')
            return redirect('project_costing:expense_list', tenant_slug=tenant.slug)
    else:
        form = ExpenseEntryForm(instance=expense, tenant=tenant)

    return render(request, 'project_costing/expenses/expense_form.html', {
        'form': form, 'is_edit': True, 'expense': expense,
    })


@login_required
def expense_delete(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    expense = get_object_or_404(ExpenseEntry.unscoped, pk=pk, tenant=tenant)

    if expense.billing_status == 'billed':
        messages.error(request, 'Cannot delete a billed expense.')
        return redirect('project_costing:expense_list', tenant_slug=tenant.slug)

    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense entry deleted.')
        return redirect('project_costing:expense_list', tenant_slug=tenant.slug)

    return render(request, 'project_costing/expenses/expense_confirm_delete.html', {
        'object': expense,
    })

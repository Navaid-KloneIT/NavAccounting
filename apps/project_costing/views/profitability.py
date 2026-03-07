from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import ProfitabilitySnapshotForm
from ..models import Project, ProfitabilitySnapshot, TimeEntry, ExpenseEntry


@login_required
def profitability_dashboard(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    projects = Project.objects.filter(tenant=tenant, is_active=True, status='active')

    project_data = []
    for project in projects:
        time_cost = project.time_entries.aggregate(total=Sum('total_amount'))['total'] or 0
        expense_cost = project.expense_entries.aggregate(total=Sum('amount'))['total'] or 0
        total_cost = time_cost + expense_cost
        revenue = project.invoices.exclude(status='void').aggregate(total=Sum('total_amount'))['total'] or 0
        profit = revenue - total_cost
        margin = (profit / revenue * 100) if revenue else 0

        project_data.append({
            'project': project,
            'total_cost': total_cost,
            'revenue': revenue,
            'profit': profit,
            'margin': margin,
            'budget_used': (total_cost / project.budget_amount * 100) if project.budget_amount else 0,
        })

    return render(request, 'project_costing/profitability/profitability_dashboard.html', {
        'project_data': project_data,
    })


@login_required
def profitability_detail(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)

    time_cost = project.time_entries.aggregate(
        total_hours=Sum('hours'), total_amount=Sum('total_amount')
    )
    expense_cost = project.expense_entries.aggregate(total_amount=Sum('amount'))
    invoice_revenue = project.invoices.exclude(status='void').aggregate(
        total=Sum('total_amount')
    )

    total_cost = (time_cost['total_amount'] or 0) + (expense_cost['total_amount'] or 0)
    revenue = invoice_revenue['total'] or 0
    profit = revenue - total_cost

    snapshots = ProfitabilitySnapshot.unscoped.filter(project=project).order_by('-snapshot_date')[:10]

    # Cost breakdown by WBS
    wbs_costs = TimeEntry.unscoped.filter(project=project).values(
        'wbs_element__code', 'wbs_element__name'
    ).annotate(
        total_hours=Sum('hours'), total_amount=Sum('total_amount')
    ).order_by('wbs_element__code')

    return render(request, 'project_costing/profitability/profitability_detail.html', {
        'project': project,
        'time_cost': time_cost,
        'expense_cost': expense_cost,
        'total_cost': total_cost,
        'revenue': revenue,
        'profit': profit,
        'snapshots': snapshots,
        'wbs_costs': wbs_costs,
    })


@login_required
def snapshot_create(request, tenant_slug, project_pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    project = get_object_or_404(Project.unscoped, pk=project_pk, tenant=tenant)

    if request.method == 'POST':
        form = ProfitabilitySnapshotForm(request.POST, tenant=tenant)
        if form.is_valid():
            snapshot = form.save(commit=False)
            snapshot.tenant = tenant
            snapshot.project = project
            snapshot.save()
            messages.success(request, 'Profitability snapshot created.')
            return redirect('project_costing:profitability_detail', tenant_slug=tenant.slug, project_pk=project.pk)
    else:
        form = ProfitabilitySnapshotForm(tenant=tenant)

    return render(request, 'project_costing/profitability/snapshot_form.html', {
        'form': form, 'project': project,
    })


@login_required
def snapshot_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ProfitabilitySnapshot.objects.filter(tenant=tenant).select_related('project', 'fiscal_period')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'project_costing/profitability/snapshot_list.html', {
        'snapshots': page_obj,
        'page_obj': page_obj,
    })

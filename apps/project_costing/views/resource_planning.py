from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import ResourceAssignmentForm
from ..models import Project, ResourceAssignment


@login_required
def assignment_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ResourceAssignment.objects.filter(tenant=tenant).select_related(
        'project', 'employee', 'wbs_element'
    )

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search) |
            Q(project__project_number__icontains=search) |
            Q(role__icontains=search)
        )

    project_filter = request.GET.get('project', '')
    if project_filter:
        qs = qs.filter(project_id=project_filter)

    active_filter = request.GET.get('active', '')
    if active_filter == 'yes':
        qs = qs.filter(is_active=True)
    elif active_filter == 'no':
        qs = qs.filter(is_active=False)

    projects = Project.objects.filter(tenant=tenant, is_active=True)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'project_costing/resources/assignment_list.html', {
        'assignments': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'projects': projects,
    })


@login_required
def assignment_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ResourceAssignmentForm(request.POST, tenant=tenant)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.tenant = tenant
            assignment.save()
            messages.success(request, 'Resource assignment created.')
            return redirect('project_costing:assignment_list', tenant_slug=tenant.slug)
    else:
        form = ResourceAssignmentForm(tenant=tenant)

    return render(request, 'project_costing/resources/assignment_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def assignment_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    assignment = get_object_or_404(ResourceAssignment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ResourceAssignmentForm(request.POST, instance=assignment, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource assignment updated.')
            return redirect('project_costing:assignment_list', tenant_slug=tenant.slug)
    else:
        form = ResourceAssignmentForm(instance=assignment, tenant=tenant)

    return render(request, 'project_costing/resources/assignment_form.html', {
        'form': form, 'is_edit': True, 'assignment': assignment,
    })


@login_required
def assignment_delete(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    assignment = get_object_or_404(ResourceAssignment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Resource assignment deleted.')
        return redirect('project_costing:assignment_list', tenant_slug=tenant.slug)

    return render(request, 'project_costing/resources/assignment_confirm_delete.html', {
        'object': assignment,
    })


@login_required
def utilization_report(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    from apps.payroll.models import Employee

    employees = Employee.objects.filter(tenant=tenant, is_active=True)

    employee_data = []
    for emp in employees:
        assignments = ResourceAssignment.unscoped.filter(
            employee=emp, is_active=True
        )
        total_allocation = assignments.aggregate(
            total=Sum('allocation_percentage')
        )['total'] or 0
        total_planned = assignments.aggregate(
            total=Sum('planned_hours')
        )['total'] or 0
        total_actual = assignments.aggregate(
            total=Sum('actual_hours')
        )['total'] or 0

        employee_data.append({
            'employee': emp,
            'assignments_count': assignments.count(),
            'total_allocation': total_allocation,
            'total_planned': total_planned,
            'total_actual': total_actual,
            'utilization': (total_actual / total_planned * 100) if total_planned else 0,
        })

    return render(request, 'project_costing/resources/utilization_report.html', {
        'employee_data': employee_data,
    })

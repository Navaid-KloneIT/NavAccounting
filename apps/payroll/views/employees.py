from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import EmployeeForm
from ..models import Employee


@login_required
def employee_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Employee.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(employee_number__icontains=search) |
            Q(department__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    department_filter = request.GET.get('department', '')
    if department_filter:
        qs = qs.filter(department=department_filter)

    pay_type_filter = request.GET.get('pay_type', '')
    if pay_type_filter:
        qs = qs.filter(pay_type=pay_type_filter)

    # Get distinct departments for filter dropdown
    departments = Employee.objects.filter(
        tenant=tenant
    ).exclude(department='').values_list('department', flat=True).distinct().order_by('department')

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/employees/employee_list.html', {
        'employees': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'departments': departments,
    })


@login_required
def employee_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, tenant=tenant)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.tenant = tenant
            employee.employee_number = Employee.generate_employee_number(tenant)
            employee.save()
            messages.success(request, f'Employee "{employee.full_name}" created.')
            return redirect('payroll:employee_list', tenant_slug=tenant.slug)
    else:
        form = EmployeeForm(tenant=tenant)

    return render(request, 'payroll/employees/employee_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def employee_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    employee = get_object_or_404(Employee.unscoped, pk=pk, tenant=tenant)

    return render(request, 'payroll/employees/employee_detail.html', {
        'employee': employee,
        'tax_withholdings': employee.tax_withholdings.all(),
        'benefits': employee.benefits.select_related('benefit_plan').filter(is_active=True),
        'garnishments': employee.garnishments.filter(status='active'),
        'workers_comp': employee.workers_comp_assignments.select_related('comp_class').all(),
    })


@login_required
def employee_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    employee = get_object_or_404(Employee.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee "{employee.full_name}" updated.')
            return redirect('payroll:employee_detail', tenant_slug=tenant.slug, pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee, tenant=tenant)

    return render(request, 'payroll/employees/employee_form.html', {
        'form': form, 'is_edit': True, 'employee': employee,
    })

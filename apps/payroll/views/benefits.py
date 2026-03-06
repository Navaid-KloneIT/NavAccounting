from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import BenefitPlanForm, EmployeeBenefitForm
from ..models import BenefitPlan, EmployeeBenefit


# -------------------------------------------------------------------------
# Benefit Plans
# -------------------------------------------------------------------------

@login_required
def benefit_plan_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = BenefitPlan.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/benefits/benefit_list.html', {
        'plans': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def benefit_plan_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BenefitPlanForm(request.POST, tenant=tenant)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.tenant = tenant
            plan.save()
            messages.success(request, f'Benefit plan "{plan.name}" created.')
            return redirect('payroll:benefit_plan_list', tenant_slug=tenant.slug)
    else:
        form = BenefitPlanForm(tenant=tenant)

    return render(request, 'payroll/benefits/benefit_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def benefit_plan_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    plan = get_object_or_404(BenefitPlan.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BenefitPlanForm(request.POST, instance=plan, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Benefit plan "{plan.name}" updated.')
            return redirect('payroll:benefit_plan_list', tenant_slug=tenant.slug)
    else:
        form = BenefitPlanForm(instance=plan, tenant=tenant)

    return render(request, 'payroll/benefits/benefit_form.html', {
        'form': form, 'is_edit': True, 'plan': plan,
    })


@login_required
def benefit_plan_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    plan = get_object_or_404(BenefitPlan.unscoped, pk=pk, tenant=tenant)
    enrollments = plan.enrollments.select_related('employee').filter(is_active=True)

    return render(request, 'payroll/benefits/benefit_detail.html', {
        'plan': plan,
        'enrollments': enrollments,
    })


# -------------------------------------------------------------------------
# Employee Benefits (Enrollment)
# -------------------------------------------------------------------------

@login_required
def enrollment_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = EmployeeBenefitForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee enrolled in benefit plan.')
            return redirect('payroll:benefit_plan_list', tenant_slug=tenant.slug)
    else:
        form = EmployeeBenefitForm(tenant=tenant)

    return render(request, 'payroll/benefits/enrollment_form.html', {
        'form': form,
    })


@login_required
def enrollment_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    enrollment = get_object_or_404(EmployeeBenefit, pk=pk)

    if request.method == 'POST':
        form = EmployeeBenefitForm(request.POST, instance=enrollment, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enrollment updated.')
            return redirect('payroll:benefit_plan_detail', tenant_slug=tenant.slug,
                            pk=enrollment.benefit_plan.pk)
    else:
        form = EmployeeBenefitForm(instance=enrollment, tenant=tenant)

    return render(request, 'payroll/benefits/enrollment_form.html', {
        'form': form, 'enrollment': enrollment,
    })

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import WorkforcePlanForm, WorkforcePlanPositionFormSet
from ..models import WorkforcePlan
from ..services import recalculate_workforce_plan


@login_required
def workforce_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = WorkforcePlan.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(plan_number__icontains=search) |
            Q(name__icontains=search) |
            Q(department__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'budgeting/workforce/workforce_list.html', {
        'plans': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': WorkforcePlan.STATUS_CHOICES,
    })


@login_required
def workforce_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = WorkforcePlanForm(request.POST, tenant=tenant)
        formset = WorkforcePlanPositionFormSet(request.POST, prefix='positions', form_kwargs={'tenant': tenant})
        if form.is_valid() and formset.is_valid():
            plan = form.save(commit=False)
            plan.tenant = tenant
            plan.plan_number = WorkforcePlan.generate_plan_number(tenant)
            plan.created_by = request.user
            plan.save()
            formset.instance = plan
            positions = formset.save(commit=False)
            for pos in positions:
                pos.tenant = tenant
                pos.save()
            for obj in formset.deleted_objects:
                obj.delete()
            recalculate_workforce_plan(plan)
            messages.success(request, f'Workforce plan "{plan.name}" created.')
            return redirect('budgeting:workforce_detail', tenant_slug=tenant.slug, pk=plan.pk)
    else:
        form = WorkforcePlanForm(tenant=tenant)
        formset = WorkforcePlanPositionFormSet(prefix='positions', form_kwargs={'tenant': tenant})

    return render(request, 'budgeting/workforce/workforce_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def workforce_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    plan = get_object_or_404(WorkforcePlan.unscoped, pk=pk, tenant=tenant)
    positions = plan.positions.select_related('gl_salary_account', 'gl_benefit_account').all()

    return render(request, 'budgeting/workforce/workforce_detail.html', {
        'plan': plan,
        'positions': positions,
    })


@login_required
def workforce_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    plan = get_object_or_404(WorkforcePlan.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = WorkforcePlanForm(request.POST, instance=plan, tenant=tenant)
        formset = WorkforcePlanPositionFormSet(
            request.POST, instance=plan, prefix='positions',
            form_kwargs={'tenant': tenant},
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            positions = formset.save(commit=False)
            for pos in positions:
                pos.tenant = tenant
                pos.save()
            for obj in formset.deleted_objects:
                obj.delete()
            recalculate_workforce_plan(plan)
            messages.success(request, f'Workforce plan "{plan.name}" updated.')
            return redirect('budgeting:workforce_detail', tenant_slug=tenant.slug, pk=plan.pk)
    else:
        form = WorkforcePlanForm(instance=plan, tenant=tenant)
        formset = WorkforcePlanPositionFormSet(
            instance=plan, prefix='positions',
            form_kwargs={'tenant': tenant},
        )

    return render(request, 'budgeting/workforce/workforce_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'plan': plan,
    })

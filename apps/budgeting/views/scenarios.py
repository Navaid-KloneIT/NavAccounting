from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import ScenarioForm, ScenarioAdjustmentFormSet
from ..models import ScenarioModel
from ..services import calculate_scenario


@login_required
def scenario_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ScenarioModel.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(scenario_number__icontains=search) |
            Q(name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    scenario_type_filter = request.GET.get('scenario_type', '')
    if scenario_type_filter:
        qs = qs.filter(scenario_type=scenario_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'budgeting/scenarios/scenario_list.html', {
        'scenarios': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': ScenarioModel.STATUS_CHOICES,
        'scenario_type_choices': ScenarioModel.SCENARIO_TYPE_CHOICES,
    })


@login_required
def scenario_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ScenarioForm(request.POST, tenant=tenant)
        formset = ScenarioAdjustmentFormSet(request.POST, prefix='adjustments', form_kwargs={'tenant': tenant})
        if form.is_valid() and formset.is_valid():
            scenario = form.save(commit=False)
            scenario.tenant = tenant
            scenario.scenario_number = ScenarioModel.generate_scenario_number(tenant)
            scenario.created_by = request.user
            scenario.save()
            formset.instance = scenario
            adjustments = formset.save(commit=False)
            for adj in adjustments:
                adj.tenant = tenant
                adj.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Scenario "{scenario.name}" created.')
            return redirect('budgeting:scenario_detail', tenant_slug=tenant.slug, pk=scenario.pk)
    else:
        form = ScenarioForm(tenant=tenant)
        formset = ScenarioAdjustmentFormSet(prefix='adjustments', form_kwargs={'tenant': tenant})

    return render(request, 'budgeting/scenarios/scenario_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def scenario_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    scenario = get_object_or_404(ScenarioModel.unscoped, pk=pk, tenant=tenant)
    adjustments = scenario.adjustments.select_related('gl_account', 'fiscal_period').all()

    return render(request, 'budgeting/scenarios/scenario_detail.html', {
        'scenario': scenario,
        'adjustments': adjustments,
    })


@login_required
def scenario_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    scenario = get_object_or_404(ScenarioModel.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ScenarioForm(request.POST, instance=scenario, tenant=tenant)
        formset = ScenarioAdjustmentFormSet(
            request.POST, instance=scenario, prefix='adjustments',
            form_kwargs={'tenant': tenant},
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            adjustments = formset.save(commit=False)
            for adj in adjustments:
                adj.tenant = tenant
                adj.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Scenario "{scenario.name}" updated.')
            return redirect('budgeting:scenario_detail', tenant_slug=tenant.slug, pk=scenario.pk)
    else:
        form = ScenarioForm(instance=scenario, tenant=tenant)
        formset = ScenarioAdjustmentFormSet(
            instance=scenario, prefix='adjustments',
            form_kwargs={'tenant': tenant},
        )

    return render(request, 'budgeting/scenarios/scenario_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'scenario': scenario,
    })


@login_required
def scenario_calculate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    scenario = get_object_or_404(ScenarioModel.unscoped, pk=pk, tenant=tenant)
    calculate_scenario(scenario, tenant)
    messages.success(request, f'Scenario "{scenario.name}" calculated.')
    return redirect('budgeting:scenario_detail', tenant_slug=tenant.slug, pk=scenario.pk)

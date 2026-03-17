from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import PlanningDriverForm, PlanningDriverPeriodFormSet
from ..models import PlanningDriver
from ..services import calculate_driver_periods


@login_required
def driver_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = PlanningDriver.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(driver_number__icontains=search) |
            Q(name__icontains=search)
        )

    driver_type_filter = request.GET.get('driver_type', '')
    if driver_type_filter:
        qs = qs.filter(driver_type=driver_type_filter)

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_drivers = PlanningDriver.objects.filter(tenant=tenant)
    return render(request, 'budgeting/drivers/driver_list.html', {
        'drivers': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'active_count': all_drivers.filter(is_active=True).count(),
        'inactive_count': all_drivers.filter(is_active=False).count(),
        'driver_type_choices': PlanningDriver.DRIVER_TYPE_CHOICES,
    })


@login_required
def driver_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PlanningDriverForm(request.POST, tenant=tenant)
        formset = PlanningDriverPeriodFormSet(request.POST, prefix='periods', form_kwargs={'tenant': tenant})
        if form.is_valid() and formset.is_valid():
            driver = form.save(commit=False)
            driver.tenant = tenant
            driver.driver_number = PlanningDriver.generate_driver_number(tenant)
            driver.save()
            formset.instance = driver
            periods = formset.save(commit=False)
            for period in periods:
                period.tenant = tenant
                period.save()
            for obj in formset.deleted_objects:
                obj.delete()
            calculate_driver_periods(driver)
            messages.success(request, f'Driver "{driver.name}" created.')
            return redirect('budgeting:driver_detail', tenant_slug=tenant.slug, pk=driver.pk)
    else:
        form = PlanningDriverForm(tenant=tenant)
        formset = PlanningDriverPeriodFormSet(prefix='periods', form_kwargs={'tenant': tenant})

    return render(request, 'budgeting/drivers/driver_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def driver_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    driver = get_object_or_404(PlanningDriver.unscoped, pk=pk, tenant=tenant)
    periods = driver.periods.select_related('fiscal_period').all()

    return render(request, 'budgeting/drivers/driver_detail.html', {
        'driver': driver,
        'periods': periods,
    })


@login_required
def driver_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    driver = get_object_or_404(PlanningDriver.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = PlanningDriverForm(request.POST, instance=driver, tenant=tenant)
        formset = PlanningDriverPeriodFormSet(
            request.POST, instance=driver, prefix='periods',
            form_kwargs={'tenant': tenant},
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            periods = formset.save(commit=False)
            for period in periods:
                period.tenant = tenant
                period.save()
            for obj in formset.deleted_objects:
                obj.delete()
            calculate_driver_periods(driver)
            messages.success(request, f'Driver "{driver.name}" updated.')
            return redirect('budgeting:driver_detail', tenant_slug=tenant.slug, pk=driver.pk)
    else:
        form = PlanningDriverForm(instance=driver, tenant=tenant)
        formset = PlanningDriverPeriodFormSet(
            instance=driver, prefix='periods',
            form_kwargs={'tenant': tenant},
        )

    return render(request, 'budgeting/drivers/driver_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'driver': driver,
    })


@login_required
def driver_calculate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    driver = get_object_or_404(PlanningDriver.unscoped, pk=pk, tenant=tenant)
    calculate_driver_periods(driver)
    messages.success(request, f'Driver "{driver.name}" periods recalculated.')
    return redirect('budgeting:driver_detail', tenant_slug=tenant.slug, pk=driver.pk)

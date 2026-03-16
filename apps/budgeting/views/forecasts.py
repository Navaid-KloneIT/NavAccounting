from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import RollingForecastForm, ForecastLineItemFormSet
from ..models import RollingForecast


@login_required
def forecast_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = RollingForecast.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(forecast_number__icontains=search) |
            Q(name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    forecast_type_filter = request.GET.get('forecast_type', '')
    if forecast_type_filter:
        qs = qs.filter(forecast_type=forecast_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'budgeting/forecasts/forecast_list.html', {
        'forecasts': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'status_choices': RollingForecast.STATUS_CHOICES,
        'forecast_type_choices': RollingForecast.FORECAST_TYPE_CHOICES,
    })


@login_required
def forecast_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = RollingForecastForm(request.POST, tenant=tenant)
        formset = ForecastLineItemFormSet(request.POST, prefix='lines', form_kwargs={'tenant': tenant})
        if form.is_valid() and formset.is_valid():
            forecast = form.save(commit=False)
            forecast.tenant = tenant
            forecast.forecast_number = RollingForecast.generate_forecast_number(tenant)
            forecast.created_by = request.user
            forecast.save()
            formset.instance = forecast
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = tenant
                line.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Forecast "{forecast.name}" created.')
            return redirect('budgeting:forecast_detail', tenant_slug=tenant.slug, pk=forecast.pk)
    else:
        form = RollingForecastForm(tenant=tenant)
        formset = ForecastLineItemFormSet(prefix='lines', form_kwargs={'tenant': tenant})

    return render(request, 'budgeting/forecasts/forecast_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def forecast_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    forecast = get_object_or_404(RollingForecast.unscoped, pk=pk, tenant=tenant)
    line_items = forecast.line_items.select_related('gl_account', 'fiscal_period').all()

    return render(request, 'budgeting/forecasts/forecast_detail.html', {
        'forecast': forecast,
        'line_items': line_items,
    })


@login_required
def forecast_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    forecast = get_object_or_404(RollingForecast.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = RollingForecastForm(request.POST, instance=forecast, tenant=tenant)
        formset = ForecastLineItemFormSet(
            request.POST, instance=forecast, prefix='lines',
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
            messages.success(request, f'Forecast "{forecast.name}" updated.')
            return redirect('budgeting:forecast_detail', tenant_slug=tenant.slug, pk=forecast.pk)
    else:
        form = RollingForecastForm(instance=forecast, tenant=tenant)
        formset = ForecastLineItemFormSet(
            instance=forecast, prefix='lines',
            form_kwargs={'tenant': tenant},
        )

    return render(request, 'budgeting/forecasts/forecast_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'forecast': forecast,
    })

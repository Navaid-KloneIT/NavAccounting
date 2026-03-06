from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import GarnishmentForm
from ..models import Garnishment


@login_required
def garnishment_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Garnishment.objects.filter(tenant=tenant).select_related('employee')
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search) |
            Q(case_number__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    type_filter = request.GET.get('garnishment_type', '')
    if type_filter:
        qs = qs.filter(garnishment_type=type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/garnishments/garnishment_list.html', {
        'garnishments': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def garnishment_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = GarnishmentForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, 'Garnishment created.')
            return redirect('payroll:garnishment_list', tenant_slug=tenant.slug)
    else:
        form = GarnishmentForm(tenant=tenant)

    return render(request, 'payroll/garnishments/garnishment_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def garnishment_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    garnishment = get_object_or_404(Garnishment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = GarnishmentForm(request.POST, instance=garnishment, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Garnishment updated.')
            return redirect('payroll:garnishment_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = GarnishmentForm(instance=garnishment, tenant=tenant)

    return render(request, 'payroll/garnishments/garnishment_form.html', {
        'form': form, 'is_edit': True, 'garnishment': garnishment,
    })


@login_required
def garnishment_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    garnishment = get_object_or_404(Garnishment.unscoped, pk=pk, tenant=tenant)

    return render(request, 'payroll/garnishments/garnishment_detail.html', {
        'garnishment': garnishment,
    })

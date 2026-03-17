from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import SOXControlForm, SOXControlTestForm
from ..models import SOXControl, SOXControlTest


@login_required
def sox_control_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = SOXControl.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(control_number__icontains=search) |
            Q(name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    risk_level_filter = request.GET.get('risk_level', '')
    if risk_level_filter:
        qs = qs.filter(risk_level=risk_level_filter)

    control_type_filter = request.GET.get('control_type', '')
    if control_type_filter:
        qs = qs.filter(control_type=control_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_controls = SOXControl.objects.filter(tenant=tenant)
    return render(request, 'audit/sox_controls/sox_control_list.html', {
        'controls': page_obj,
        'page_obj': page_obj,
        'total_count': all_controls.count(),
        'active_count': all_controls.filter(status='active').count(),
        'deficient_count': all_controls.filter(status='deficient').count(),
        'status_choices': SOXControl.STATUS_CHOICES,
        'risk_level_choices': SOXControl.RISK_LEVEL_CHOICES,
        'control_type_choices': SOXControl.CONTROL_TYPE_CHOICES,
    })


@login_required
def sox_control_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = SOXControlForm(request.POST)
        if form.is_valid():
            control = form.save(commit=False)
            control.tenant = tenant
            control.control_number = SOXControl.generate_control_number(tenant)
            if not control.owner_id:
                control.owner = request.user
            control.save()
            messages.success(request, f'SOX Control "{control.name}" created.')
            return redirect('audit:sox_control_detail', tenant_slug=tenant.slug, pk=control.pk)
    else:
        form = SOXControlForm()

    return render(request, 'audit/sox_controls/sox_control_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def sox_control_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    control = get_object_or_404(SOXControl.unscoped, pk=pk, tenant=tenant)
    tests = control.tests.select_related('tested_by').all()[:10]

    return render(request, 'audit/sox_controls/sox_control_detail.html', {
        'control': control,
        'tests': tests,
    })


@login_required
def sox_control_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    control = get_object_or_404(SOXControl.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = SOXControlForm(request.POST, instance=control)
        if form.is_valid():
            form.save()
            messages.success(request, f'SOX Control "{control.name}" updated.')
            return redirect('audit:sox_control_detail', tenant_slug=tenant.slug, pk=control.pk)
    else:
        form = SOXControlForm(instance=control)

    return render(request, 'audit/sox_controls/sox_control_form.html', {
        'form': form, 'is_edit': True, 'control': control,
    })


@login_required
def sox_test_create(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    control = get_object_or_404(SOXControl.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = SOXControlTestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.tenant = tenant
            test.control = control
            test.test_number = SOXControlTest.generate_test_number(tenant)
            test.save()
            control.last_tested_date = test.test_date
            control.save(update_fields=['last_tested_date', 'updated_at'])
            messages.success(request, f'Test "{test.test_number}" created for {control.name}.')
            return redirect('audit:sox_control_detail', tenant_slug=tenant.slug, pk=control.pk)
    else:
        form = SOXControlTestForm()

    return render(request, 'audit/sox_controls/sox_test_form.html', {
        'form': form, 'control': control,
    })

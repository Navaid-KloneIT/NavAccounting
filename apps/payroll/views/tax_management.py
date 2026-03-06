from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import TaxWithholdingForm, TaxRemittanceForm
from ..models import TaxWithholding, TaxRemittance
from ..services import post_tax_remittance


@login_required
def tax_withholding_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxWithholding.objects.filter(tenant=tenant).select_related('employee')
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search) |
            Q(employee__employee_number__icontains=search)
        )

    tax_type_filter = request.GET.get('tax_type', '')
    if tax_type_filter:
        qs = qs.filter(tax_type=tax_type_filter)

    employer_paid_filter = request.GET.get('employer_paid', '')
    if employer_paid_filter == 'yes':
        qs = qs.filter(is_employer_paid=True)
    elif employer_paid_filter == 'no':
        qs = qs.filter(is_employer_paid=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/tax_management/tax_list.html', {
        'withholdings': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def tax_withholding_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxWithholdingForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, 'Tax withholding created.')
            return redirect('payroll:tax_withholding_list', tenant_slug=tenant.slug)
    else:
        form = TaxWithholdingForm(tenant=tenant)

    return render(request, 'payroll/tax_management/tax_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def tax_withholding_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    withholding = get_object_or_404(TaxWithholding.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxWithholdingForm(request.POST, instance=withholding, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tax withholding updated.')
            return redirect('payroll:tax_withholding_list', tenant_slug=tenant.slug)
    else:
        form = TaxWithholdingForm(instance=withholding, tenant=tenant)

    return render(request, 'payroll/tax_management/tax_form.html', {
        'form': form, 'is_edit': True, 'withholding': withholding,
    })


# -------------------------------------------------------------------------
# Tax Remittance
# -------------------------------------------------------------------------

@login_required
def remittance_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxRemittance.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(remittance_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    tax_type_filter = request.GET.get('tax_type', '')
    if tax_type_filter:
        qs = qs.filter(tax_type=tax_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/tax_management/remittance_list.html', {
        'remittances': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def remittance_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxRemittanceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.remittance_number = TaxRemittance.generate_remittance_number(tenant)
            obj.save()
            messages.success(request, f'Tax remittance "{obj.remittance_number}" created.')
            return redirect('payroll:remittance_list', tenant_slug=tenant.slug)
    else:
        form = TaxRemittanceForm()

    return render(request, 'payroll/tax_management/remittance_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def remittance_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    remittance = get_object_or_404(TaxRemittance.unscoped, pk=pk, tenant=tenant)

    return render(request, 'payroll/tax_management/remittance_detail.html', {
        'remittance': remittance,
    })


@login_required
def remittance_pay(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    remittance = get_object_or_404(TaxRemittance.unscoped, pk=pk, tenant=tenant)
    if remittance.status != 'pending':
        messages.error(request, 'Only pending remittances can be paid.')
        return redirect('payroll:remittance_detail', tenant_slug=tenant.slug, pk=pk)

    remittance.amount_paid = remittance.amount_due
    post_tax_remittance(remittance, tenant, request.user)
    messages.success(request, f'Tax remittance "{remittance.remittance_number}" paid.')
    return redirect('payroll:remittance_detail', tenant_slug=tenant.slug, pk=pk)

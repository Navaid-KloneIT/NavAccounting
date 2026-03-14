from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import (
    IncomeTaxProvisionForm, DeferredTaxItemFormSet, ETRReconciliationFormSet,
)
from ..models import IncomeTaxProvision


@login_required
def provision_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = IncomeTaxProvision.objects.filter(tenant=tenant).select_related('fiscal_year')

    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    finalized_count = qs.filter(status='finalized').count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(provision_number__icontains=search))

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    provision_type = request.GET.get('provision_type', '')
    if provision_type:
        qs = qs.filter(provision_type=provision_type)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/provision/provision_list.html', {
        'provisions': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'finalized_count': finalized_count,
        'status_choices': IncomeTaxProvision.STATUS_CHOICES,
        'provision_type_choices': IncomeTaxProvision.PROVISION_TYPE_CHOICES,
    })


@login_required
def provision_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = IncomeTaxProvisionForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.provision_number = IncomeTaxProvision.generate_provision_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Provision "{obj.provision_number}" created.')
            return redirect('tax:provision_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = IncomeTaxProvisionForm(tenant=tenant)

    return render(request, 'tax/provision/provision_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def provision_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    provision = get_object_or_404(IncomeTaxProvision.unscoped, pk=pk, tenant=tenant)
    deferred_items = provision.deferred_items.all()
    etr_lines = provision.etr_lines.all()

    return render(request, 'tax/provision/provision_detail.html', {
        'provision': provision,
        'deferred_items': deferred_items,
        'etr_lines': etr_lines,
    })


@login_required
def provision_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    provision = get_object_or_404(IncomeTaxProvision.unscoped, pk=pk, tenant=tenant)

    if provision.status == 'finalized':
        messages.error(request, 'Finalized provisions cannot be edited.')
        return redirect('tax:provision_detail', tenant_slug=tenant.slug, pk=pk)

    if request.method == 'POST':
        form = IncomeTaxProvisionForm(request.POST, instance=provision, tenant=tenant)
        deferred_formset = DeferredTaxItemFormSet(request.POST, instance=provision, prefix='deferred')
        etr_formset = ETRReconciliationFormSet(request.POST, instance=provision, prefix='etr')
        if form.is_valid() and deferred_formset.is_valid() and etr_formset.is_valid():
            form.save()
            deferred_formset.save()
            etr_formset.save()
            messages.success(request, f'Provision "{provision.provision_number}" updated.')
            return redirect('tax:provision_detail', tenant_slug=tenant.slug, pk=provision.pk)
    else:
        form = IncomeTaxProvisionForm(instance=provision, tenant=tenant)
        deferred_formset = DeferredTaxItemFormSet(instance=provision, prefix='deferred')
        etr_formset = ETRReconciliationFormSet(instance=provision, prefix='etr')

    from apps.general_ledger.models import Account
    gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
    for f in deferred_formset.forms:
        if 'gl_account' in f.fields:
            f.fields['gl_account'].queryset = gl_qs

    return render(request, 'tax/provision/provision_edit.html', {
        'form': form,
        'deferred_formset': deferred_formset,
        'etr_formset': etr_formset,
        'is_edit': True,
        'provision': provision,
    })


@login_required
def provision_calculate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    provision = get_object_or_404(IncomeTaxProvision.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        from ..services import calculate_provision
        calculate_provision(provision, tenant)
        messages.success(request, f'Provision "{provision.provision_number}" calculated.')

    return redirect('tax:provision_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def provision_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    provision = get_object_or_404(IncomeTaxProvision.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if provision.status in ('calculated', 'reviewed'):
            from ..services import post_provision
            je = post_provision(provision, tenant, request.user)
            if je:
                messages.success(request, f'Provision posted to GL (JE: {je.entry_number}).')
            else:
                messages.error(request, 'Could not post provision. Check GL account setup.')
        else:
            messages.error(request, 'Provision must be calculated or reviewed before posting.')

    return redirect('tax:provision_detail', tenant_slug=tenant.slug, pk=pk)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import TaxReturnForm, TaxReturnLineFormSet, TaxReturnPaymentForm
from ..models import TaxReturn


@login_required
def return_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxReturn.objects.filter(tenant=tenant).select_related('jurisdiction')

    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    filed_count = qs.filter(status='filed').count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(return_number__icontains=search) |
            Q(jurisdiction__name__icontains=search)
        )

    return_type = request.GET.get('return_type', '')
    if return_type:
        qs = qs.filter(return_type=return_type)

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/tax_returns/return_list.html', {
        'returns': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'filed_count': filed_count,
        'return_type_choices': TaxReturn.RETURN_TYPE_CHOICES,
        'status_choices': TaxReturn.STATUS_CHOICES,
    })


@login_required
def return_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxReturnForm(request.POST, tenant=tenant)
        formset = TaxReturnLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.return_number = TaxReturn.generate_return_number(tenant)
            obj.created_by = request.user
            obj.save()
            formset.instance = obj
            formset.save()
            messages.success(request, f'Tax return "{obj.return_number}" created.')
            return redirect('tax:return_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = TaxReturnForm(tenant=tenant)
        formset = TaxReturnLineFormSet()

    from apps.general_ledger.models import Account
    gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
    for f in formset.forms:
        if 'gl_account' in f.fields:
            f.fields['gl_account'].queryset = gl_qs

    return render(request, 'tax/tax_returns/return_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def return_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    tax_return = get_object_or_404(TaxReturn.unscoped, pk=pk, tenant=tenant)
    lines = tax_return.lines.all()
    payments = tax_return.payments.all()

    return render(request, 'tax/tax_returns/return_detail.html', {
        'tax_return': tax_return,
        'lines': lines,
        'payments': payments,
    })


@login_required
def return_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    tax_return = get_object_or_404(TaxReturn.unscoped, pk=pk, tenant=tenant)

    if tax_return.status not in ('draft', 'calculated'):
        messages.error(request, 'Only draft or calculated returns can be edited.')
        return redirect('tax:return_detail', tenant_slug=tenant.slug, pk=pk)

    if request.method == 'POST':
        form = TaxReturnForm(request.POST, instance=tax_return, tenant=tenant)
        formset = TaxReturnLineFormSet(request.POST, instance=tax_return)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Tax return "{tax_return.return_number}" updated.')
            return redirect('tax:return_detail', tenant_slug=tenant.slug, pk=tax_return.pk)
    else:
        form = TaxReturnForm(instance=tax_return, tenant=tenant)
        formset = TaxReturnLineFormSet(instance=tax_return)

    from apps.general_ledger.models import Account
    gl_qs = Account.unscoped.filter(tenant=tenant, is_active=True, is_header=False)
    for f in formset.forms:
        if 'gl_account' in f.fields:
            f.fields['gl_account'].queryset = gl_qs

    return render(request, 'tax/tax_returns/return_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'tax_return': tax_return,
    })


@login_required
def return_calculate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    tax_return = get_object_or_404(TaxReturn.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        from ..services import calculate_tax_return
        calculate_tax_return(tax_return, tenant)
        messages.success(request, f'Tax return "{tax_return.return_number}" calculated.')

    return redirect('tax:return_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def return_file(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    tax_return = get_object_or_404(TaxReturn.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if tax_return.status in ('calculated', 'reviewed'):
            tax_return.status = 'filed'
            tax_return.filed_date = timezone.now().date()
            tax_return.filed_by = request.user
            tax_return.confirmation_number = request.POST.get('confirmation_number', '')
            tax_return.save()
            messages.success(request, f'Tax return "{tax_return.return_number}" marked as filed.')
        else:
            messages.error(request, 'Return must be calculated or reviewed before filing.')

    return redirect('tax:return_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def return_payment(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    tax_return = get_object_or_404(TaxReturn.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxReturnPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.tenant = tenant
            payment.tax_return = tax_return
            payment.save()

            from ..services import post_return_payment
            post_return_payment(payment, tenant, request.user)
            messages.success(request, f'Payment of {payment.amount} recorded.')
            return redirect('tax:return_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = TaxReturnPaymentForm()

    return render(request, 'tax/tax_returns/return_payment_form.html', {
        'form': form, 'tax_return': tax_return,
    })

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import (
    TaxJurisdictionForm, TaxRateForm, TaxRuleForm,
    TaxGroupForm, TaxGroupMemberFormSet,
)
from ..models import TaxJurisdiction, TaxRate, TaxRule, TaxGroup


# =============================================================================
# Jurisdictions
# =============================================================================

@login_required
def jurisdiction_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxJurisdiction.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()
    inactive_count = qs.filter(is_active=False).count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(code__icontains=search) | Q(name__icontains=search) |
            Q(state_code__icontains=search)
        )

    # Level filter
    level = request.GET.get('level', '')
    if level:
        qs = qs.filter(jurisdiction_level=level)

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/sales_tax/jurisdiction_list.html', {
        'jurisdictions': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'level_choices': TaxJurisdiction.JURISDICTION_LEVEL_CHOICES,
    })


@login_required
def jurisdiction_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxJurisdictionForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Jurisdiction "{obj.code}" created.')
            return redirect('tax:jurisdiction_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = TaxJurisdictionForm(tenant=tenant)

    return render(request, 'tax/sales_tax/jurisdiction_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def jurisdiction_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    jurisdiction = get_object_or_404(TaxJurisdiction.unscoped, pk=pk, tenant=tenant)
    children = TaxJurisdiction.objects.filter(tenant=tenant, parent=jurisdiction)
    rates = jurisdiction.rates.filter(tenant=tenant)
    rules = jurisdiction.rules.filter(tenant=tenant)

    return render(request, 'tax/sales_tax/jurisdiction_detail.html', {
        'jurisdiction': jurisdiction,
        'children': children,
        'rates': rates,
        'rules': rules,
    })


@login_required
def jurisdiction_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    jurisdiction = get_object_or_404(TaxJurisdiction.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxJurisdictionForm(request.POST, instance=jurisdiction, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Jurisdiction "{jurisdiction.code}" updated.')
            return redirect('tax:jurisdiction_detail', tenant_slug=tenant.slug, pk=jurisdiction.pk)
    else:
        form = TaxJurisdictionForm(instance=jurisdiction, tenant=tenant)

    return render(request, 'tax/sales_tax/jurisdiction_form.html', {
        'form': form, 'is_edit': True, 'jurisdiction': jurisdiction,
    })


# =============================================================================
# Tax Rates
# =============================================================================

@login_required
def tax_rate_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxRate.objects.filter(tenant=tenant).select_related('jurisdiction')

    total_count = qs.count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(rate_name__icontains=search) | Q(jurisdiction__code__icontains=search) |
            Q(jurisdiction__name__icontains=search)
        )

    # Jurisdiction filter
    jurisdiction_id = request.GET.get('jurisdiction', '')
    if jurisdiction_id:
        qs = qs.filter(jurisdiction_id=jurisdiction_id)

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    jurisdictions = TaxJurisdiction.objects.filter(tenant=tenant, is_active=True)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/sales_tax/tax_rate_list.html', {
        'rates': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'jurisdictions': jurisdictions,
    })


@login_required
def tax_rate_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxRateForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Tax rate "{obj.rate_name}" created.')
            return redirect('tax:tax_rate_list', tenant_slug=tenant.slug)
    else:
        form = TaxRateForm(tenant=tenant)

    return render(request, 'tax/sales_tax/tax_rate_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def tax_rate_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rate = get_object_or_404(TaxRate.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxRateForm(request.POST, instance=rate, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tax rate "{rate.rate_name}" updated.')
            return redirect('tax:tax_rate_list', tenant_slug=tenant.slug)
    else:
        form = TaxRateForm(instance=rate, tenant=tenant)

    return render(request, 'tax/sales_tax/tax_rate_form.html', {
        'form': form, 'is_edit': True, 'rate': rate,
    })


# =============================================================================
# Tax Rules
# =============================================================================

@login_required
def tax_rule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxRule.objects.filter(tenant=tenant).select_related('jurisdiction')

    total_count = qs.count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(code__icontains=search) | Q(name__icontains=search) |
            Q(product_category__icontains=search)
        )

    rule_type = request.GET.get('rule_type', '')
    if rule_type:
        qs = qs.filter(rule_type=rule_type)

    jurisdiction_id = request.GET.get('jurisdiction', '')
    if jurisdiction_id:
        qs = qs.filter(jurisdiction_id=jurisdiction_id)

    jurisdictions = TaxJurisdiction.objects.filter(tenant=tenant, is_active=True)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/sales_tax/tax_rule_list.html', {
        'rules': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'rule_type_choices': TaxRule.RULE_TYPE_CHOICES,
        'jurisdictions': jurisdictions,
    })


@login_required
def tax_rule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxRuleForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Tax rule "{obj.code}" created.')
            return redirect('tax:tax_rule_list', tenant_slug=tenant.slug)
    else:
        form = TaxRuleForm(tenant=tenant)

    return render(request, 'tax/sales_tax/tax_rule_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def tax_rule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(TaxRule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxRuleForm(request.POST, instance=rule, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tax rule "{rule.code}" updated.')
            return redirect('tax:tax_rule_list', tenant_slug=tenant.slug)
    else:
        form = TaxRuleForm(instance=rule, tenant=tenant)

    return render(request, 'tax/sales_tax/tax_rule_form.html', {
        'form': form, 'is_edit': True, 'rule': rule,
    })


# =============================================================================
# Tax Groups
# =============================================================================

@login_required
def tax_group_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = TaxGroup.objects.filter(tenant=tenant)

    total_count = qs.count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search))

    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/sales_tax/tax_group_list.html', {
        'groups': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
    })


@login_required
def tax_group_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxGroupForm(request.POST)
        formset = TaxGroupMemberFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            formset.instance = obj
            formset.save()
            messages.success(request, f'Tax group "{obj.code}" created.')
            return redirect('tax:tax_group_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = TaxGroupForm()
        formset = TaxGroupMemberFormSet()

    # Filter tax_rate queryset for formset
    rate_qs = TaxRate.objects.filter(tenant=tenant, is_active=True)
    for f in formset.forms:
        f.fields['tax_rate'].queryset = rate_qs

    return render(request, 'tax/sales_tax/tax_group_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def tax_group_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    group = get_object_or_404(TaxGroup.unscoped, pk=pk, tenant=tenant)
    members = group.members.select_related('tax_rate', 'tax_rate__jurisdiction').all()

    return render(request, 'tax/sales_tax/tax_group_detail.html', {
        'group': group,
        'members': members,
    })


@login_required
def tax_group_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    group = get_object_or_404(TaxGroup.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxGroupForm(request.POST, instance=group)
        formset = TaxGroupMemberFormSet(request.POST, instance=group)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Tax group "{group.code}" updated.')
            return redirect('tax:tax_group_detail', tenant_slug=tenant.slug, pk=group.pk)
    else:
        form = TaxGroupForm(instance=group)
        formset = TaxGroupMemberFormSet(instance=group)

    rate_qs = TaxRate.objects.filter(tenant=tenant, is_active=True)
    for f in formset.forms:
        f.fields['tax_rate'].queryset = rate_qs

    return render(request, 'tax/sales_tax/tax_group_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'group': group,
    })

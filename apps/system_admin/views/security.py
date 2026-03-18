from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import MFAConfigurationForm, IPRestrictionForm, SessionPolicyForm
from ..models import MFAConfiguration, IPRestriction, SessionPolicy


# ──────────────────────────────────────────────
# MFA Configuration Views
# ──────────────────────────────────────────────

@login_required
def mfa_config_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = MFAConfiguration.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(config_number__icontains=search) | Q(name__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    method_filter = request.GET.get('mfa_method', '')
    if method_filter:
        qs = qs.filter(mfa_method=method_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = MFAConfiguration.objects.filter(tenant=tenant)
    return render(request, 'system_admin/security/mfa_config_list.html', {
        'configs': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(status='active').count(),
        'inactive_count': all_items.filter(status='inactive').count(),
        'status_choices': MFAConfiguration.STATUS_CHOICES,
        'method_choices': MFAConfiguration.MFA_METHOD_CHOICES,
    })


@login_required
def mfa_config_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = MFAConfigurationForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.config_number = MFAConfiguration.generate_config_number(tenant)
            obj.save()
            form.save_m2m()
            messages.success(request, f'MFA Configuration "{obj.name}" created.')
            return redirect('system_admin:mfa_config_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = MFAConfigurationForm()

    return render(request, 'system_admin/security/mfa_config_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def mfa_config_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    config = get_object_or_404(MFAConfiguration.unscoped, pk=pk, tenant=tenant)
    return render(request, 'system_admin/security/mfa_config_detail.html', {
        'config': config,
    })


@login_required
def mfa_config_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    config = get_object_or_404(MFAConfiguration.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = MFAConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, f'MFA Configuration "{config.name}" updated.')
            return redirect('system_admin:mfa_config_detail', tenant_slug=tenant.slug, pk=config.pk)
    else:
        form = MFAConfigurationForm(instance=config)

    return render(request, 'system_admin/security/mfa_config_form.html', {
        'form': form, 'is_edit': True, 'config': config,
    })


# ──────────────────────────────────────────────
# IP Restriction Views
# ──────────────────────────────────────────────

@login_required
def ip_restriction_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = IPRestriction.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(restriction_number__icontains=search) | Q(name__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    rule_type_filter = request.GET.get('rule_type', '')
    if rule_type_filter:
        qs = qs.filter(rule_type=rule_type_filter)

    applies_to_filter = request.GET.get('applies_to', '')
    if applies_to_filter:
        qs = qs.filter(applies_to=applies_to_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = IPRestriction.objects.filter(tenant=tenant)
    return render(request, 'system_admin/security/ip_restriction_list.html', {
        'restrictions': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(status='active').count(),
        'inactive_count': all_items.filter(status='inactive').count(),
        'rule_type_choices': IPRestriction.RULE_TYPE_CHOICES,
        'applies_to_choices': IPRestriction.APPLIES_TO_CHOICES,
        'status_choices': IPRestriction.STATUS_CHOICES,
    })


@login_required
def ip_restriction_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = IPRestrictionForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.restriction_number = IPRestriction.generate_restriction_number(tenant)
            obj.save()
            form.save_m2m()
            messages.success(request, f'IP Restriction "{obj.name}" created.')
            return redirect('system_admin:ip_restriction_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = IPRestrictionForm()

    return render(request, 'system_admin/security/ip_restriction_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def ip_restriction_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    restriction = get_object_or_404(IPRestriction.unscoped, pk=pk, tenant=tenant)
    return render(request, 'system_admin/security/ip_restriction_detail.html', {
        'restriction': restriction,
    })


@login_required
def ip_restriction_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    restriction = get_object_or_404(IPRestriction.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = IPRestrictionForm(request.POST, instance=restriction)
        if form.is_valid():
            form.save()
            messages.success(request, f'IP Restriction "{restriction.name}" updated.')
            return redirect('system_admin:ip_restriction_detail', tenant_slug=tenant.slug, pk=restriction.pk)
    else:
        form = IPRestrictionForm(instance=restriction)

    return render(request, 'system_admin/security/ip_restriction_form.html', {
        'form': form, 'is_edit': True, 'restriction': restriction,
    })


# ──────────────────────────────────────────────
# Session Policy Views
# ──────────────────────────────────────────────

@login_required
def session_policy_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = SessionPolicy.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(policy_number__icontains=search) | Q(name__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = SessionPolicy.objects.filter(tenant=tenant)
    return render(request, 'system_admin/security/session_policy_list.html', {
        'policies': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(status='active').count(),
        'inactive_count': all_items.filter(status='inactive').count(),
        'status_choices': SessionPolicy.STATUS_CHOICES,
    })


@login_required
def session_policy_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = SessionPolicyForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.policy_number = SessionPolicy.generate_policy_number(tenant)
            obj.save()
            form.save_m2m()
            messages.success(request, f'Session Policy "{obj.name}" created.')
            return redirect('system_admin:session_policy_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = SessionPolicyForm()

    return render(request, 'system_admin/security/session_policy_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def session_policy_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    policy = get_object_or_404(SessionPolicy.unscoped, pk=pk, tenant=tenant)
    return render(request, 'system_admin/security/session_policy_detail.html', {
        'policy': policy,
    })


@login_required
def session_policy_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    policy = get_object_or_404(SessionPolicy.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = SessionPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, f'Session Policy "{policy.name}" updated.')
            return redirect('system_admin:session_policy_detail', tenant_slug=tenant.slug, pk=policy.pk)
    else:
        form = SessionPolicyForm(instance=policy)

    return render(request, 'system_admin/security/session_policy_form.html', {
        'form': form, 'is_edit': True, 'policy': policy,
    })

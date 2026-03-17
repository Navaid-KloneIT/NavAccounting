from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant
from ..forms import ExceptionRuleForm
from ..models import ExceptionRule, AuditException
from ..services import run_exception_scan


@login_required
def exception_rule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ExceptionRule.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(rule_number__icontains=search) |
            Q(name__icontains=search)
        )

    rule_type_filter = request.GET.get('rule_type', '')
    if rule_type_filter:
        qs = qs.filter(rule_type=rule_type_filter)

    severity_filter = request.GET.get('severity', '')
    if severity_filter:
        qs = qs.filter(severity=severity_filter)

    active_filter = request.GET.get('is_active', '')
    if active_filter == 'active':
        qs = qs.filter(is_active=True)
    elif active_filter == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_rules = ExceptionRule.objects.filter(tenant=tenant)
    return render(request, 'audit/exceptions/exception_rule_list.html', {
        'rules': page_obj,
        'page_obj': page_obj,
        'total_count': all_rules.count(),
        'active_count': all_rules.filter(is_active=True).count(),
        'rule_type_choices': ExceptionRule.RULE_TYPE_CHOICES,
        'severity_choices': ExceptionRule.SEVERITY_CHOICES,
    })


@login_required
def exception_rule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ExceptionRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.tenant = tenant
            rule.rule_number = ExceptionRule.generate_rule_number(tenant)
            rule.save()
            messages.success(request, f'Exception Rule "{rule.name}" created.')
            return redirect('audit:exception_rule_detail', tenant_slug=tenant.slug, pk=rule.pk)
    else:
        form = ExceptionRuleForm()

    return render(request, 'audit/exceptions/exception_rule_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def exception_rule_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(ExceptionRule.unscoped, pk=pk, tenant=tenant)
    exceptions = rule.exceptions.all()[:10]

    return render(request, 'audit/exceptions/exception_rule_detail.html', {
        'rule': rule,
        'exceptions': exceptions,
    })


@login_required
def exception_rule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(ExceptionRule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ExceptionRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Exception Rule "{rule.name}" updated.')
            return redirect('audit:exception_rule_detail', tenant_slug=tenant.slug, pk=rule.pk)
    else:
        form = ExceptionRuleForm(instance=rule)

    return render(request, 'audit/exceptions/exception_rule_form.html', {
        'form': form, 'is_edit': True, 'rule': rule,
    })


@login_required
def exception_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AuditException.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(exception_number__icontains=search) |
            Q(description__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    severity_filter = request.GET.get('severity', '')
    if severity_filter:
        qs = qs.filter(severity=severity_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_exceptions = AuditException.objects.filter(tenant=tenant)
    return render(request, 'audit/exceptions/exception_list.html', {
        'exceptions': page_obj,
        'page_obj': page_obj,
        'total_count': all_exceptions.count(),
        'open_count': all_exceptions.filter(status='open').count(),
        'critical_count': all_exceptions.filter(severity='critical', status='open').count(),
        'status_choices': AuditException.STATUS_CHOICES,
        'severity_choices': AuditException.SEVERITY_CHOICES,
    })


@login_required
def exception_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    exception = get_object_or_404(AuditException.unscoped, pk=pk, tenant=tenant)

    return render(request, 'audit/exceptions/exception_detail.html', {
        'exception': exception,
    })


@login_required
def exception_resolve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:exception_list', tenant_slug=tenant.slug)

    exception = get_object_or_404(AuditException.unscoped, pk=pk, tenant=tenant)

    if exception.status in ['open', 'investigating']:
        exception.status = 'resolved'
        exception.resolved_by = request.user
        exception.resolved_at = timezone.now()
        exception.save(update_fields=['status', 'resolved_by', 'resolved_at', 'updated_at'])
        messages.success(request, f'Exception "{exception.exception_number}" marked as resolved.')
    else:
        messages.warning(request, f'Exception "{exception.exception_number}" cannot be resolved from its current status.')

    return redirect('audit:exception_detail', tenant_slug=tenant.slug, pk=exception.pk)


@login_required
def exception_run_scan(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:exception_list', tenant_slug=tenant.slug)

    count = run_exception_scan(tenant, request.user)
    messages.success(request, f'Exception scan complete. {count} new exception(s) detected.')

    return redirect('audit:exception_list', tenant_slug=tenant.slug)

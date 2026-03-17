from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant
from ..forms import SoDRuleForm
from ..models import SoDRule, SoDViolation
from ..services import scan_sod_conflicts


@login_required
def sod_rule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = SoDRule.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(rule_number__icontains=search) |
            Q(name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    risk_level_filter = request.GET.get('risk_level', '')
    if risk_level_filter:
        qs = qs.filter(risk_level=risk_level_filter)

    enforcement_filter = request.GET.get('enforcement', '')
    if enforcement_filter:
        qs = qs.filter(enforcement=enforcement_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_rules = SoDRule.objects.filter(tenant=tenant)
    return render(request, 'audit/sod/sod_rule_list.html', {
        'rules': page_obj,
        'page_obj': page_obj,
        'total_count': all_rules.count(),
        'active_count': all_rules.filter(status='active').count(),
        'under_review_count': all_rules.filter(status='under_review').count(),
        'status_choices': SoDRule.STATUS_CHOICES,
        'risk_level_choices': SoDRule.RISK_LEVEL_CHOICES,
        'enforcement_choices': SoDRule.ENFORCEMENT_CHOICES,
    })


@login_required
def sod_rule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = SoDRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.tenant = tenant
            rule.rule_number = SoDRule.generate_rule_number(tenant)
            rule.save()
            messages.success(request, f'SoD Rule "{rule.name}" created.')
            return redirect('audit:sod_rule_detail', tenant_slug=tenant.slug, pk=rule.pk)
    else:
        form = SoDRuleForm()

    return render(request, 'audit/sod/sod_rule_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def sod_rule_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(SoDRule.unscoped, pk=pk, tenant=tenant)
    violations = rule.violations.select_related('user').all()[:10]

    return render(request, 'audit/sod/sod_rule_detail.html', {
        'rule': rule,
        'violations': violations,
    })


@login_required
def sod_rule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    rule = get_object_or_404(SoDRule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = SoDRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f'SoD Rule "{rule.name}" updated.')
            return redirect('audit:sod_rule_detail', tenant_slug=tenant.slug, pk=rule.pk)
    else:
        form = SoDRuleForm(instance=rule)

    return render(request, 'audit/sod/sod_rule_form.html', {
        'form': form, 'is_edit': True, 'rule': rule,
    })


@login_required
def sod_violation_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = SoDViolation.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(violation_number__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_violations = SoDViolation.objects.filter(tenant=tenant)
    return render(request, 'audit/sod/sod_violation_list.html', {
        'violations': page_obj,
        'page_obj': page_obj,
        'total_count': all_violations.count(),
        'open_count': all_violations.filter(status='open').count(),
        'mitigated_count': all_violations.filter(status='mitigated').count(),
        'status_choices': SoDViolation.STATUS_CHOICES,
    })


@login_required
def sod_violation_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    violation = get_object_or_404(SoDViolation.unscoped, pk=pk, tenant=tenant)

    return render(request, 'audit/sod/sod_violation_detail.html', {
        'violation': violation,
    })


@login_required
def sod_violation_resolve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:sod_violation_list', tenant_slug=tenant.slug)

    violation = get_object_or_404(SoDViolation.unscoped, pk=pk, tenant=tenant)

    if violation.status in ('open', 'acknowledged'):
        violation.status = 'mitigated'
        violation.resolved_by = request.user
        violation.resolved_at = timezone.now()
        violation.save(update_fields=['status', 'resolved_by', 'resolved_at', 'updated_at'])
        messages.success(request, f'Violation "{violation.violation_number}" marked as mitigated.')
    else:
        messages.warning(request, f'Violation "{violation.violation_number}" cannot be resolved from its current status.')

    return redirect('audit:sod_violation_detail', tenant_slug=tenant.slug, pk=violation.pk)


@login_required
def sod_scan(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:sod_rule_list', tenant_slug=tenant.slug)

    count = scan_sod_conflicts(tenant)
    messages.success(request, f'SoD scan complete. {count} new violation(s) detected.')

    return redirect('audit:sod_violation_list', tenant_slug=tenant.slug)

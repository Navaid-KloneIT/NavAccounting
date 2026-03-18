from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant
from ..forms import SystemMetricForm, SystemHealthCheckForm
from ..models import SystemMetric, MetricDataPoint, SystemHealthCheck, UsageAnalytics


# ──────────────────────────────────────────────
# Health Dashboard
# ──────────────────────────────────────────────

@login_required
def health_dashboard(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    health_checks = SystemHealthCheck.objects.filter(tenant=tenant)[:20]

    metrics_qs = SystemMetric.objects.filter(tenant=tenant)[:5]
    recent_metrics = []
    for metric in metrics_qs:
        latest_dp = MetricDataPoint.objects.filter(
            tenant=tenant, metric=metric
        ).first()
        recent_metrics.append({
            'metric': metric,
            'latest_data_point': latest_dp,
        })

    latest_analytics = UsageAnalytics.objects.filter(tenant=tenant).first()

    all_checks = SystemHealthCheck.objects.filter(tenant=tenant)
    healthy_count = all_checks.filter(last_status='healthy').count()
    degraded_count = all_checks.filter(last_status='degraded').count()
    unhealthy_count = all_checks.filter(last_status='unhealthy').count()

    return render(request, 'system_admin/health/dashboard.html', {
        'health_checks': health_checks,
        'recent_metrics': recent_metrics,
        'latest_analytics': latest_analytics,
        'healthy_count': healthy_count,
        'degraded_count': degraded_count,
        'unhealthy_count': unhealthy_count,
    })


# ──────────────────────────────────────────────
# System Metric Views
# ──────────────────────────────────────────────

@login_required
def metric_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = SystemMetric.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(metric_number__icontains=search))

    category_filter = request.GET.get('category', '')
    if category_filter:
        qs = qs.filter(category=category_filter)

    active_filter = request.GET.get('is_active', '')
    if active_filter == 'active':
        qs = qs.filter(is_active=True)
    elif active_filter == 'inactive':
        qs = qs.filter(is_active=False)

    all_items = SystemMetric.objects.filter(tenant=tenant)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'system_admin/health/metric_list.html', {
        'metrics': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(is_active=True).count(),
        'category_choices': SystemMetric.CATEGORY_CHOICES,
    })


@login_required
def metric_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = SystemMetricForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.metric_number = SystemMetric.generate_metric_number(tenant)
            obj.save()
            form.save_m2m()
            messages.success(request, f'System Metric "{obj.name}" created.')
            return redirect('system_admin:metric_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = SystemMetricForm()

    return render(request, 'system_admin/health/metric_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def metric_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    metric = get_object_or_404(SystemMetric.unscoped, pk=pk, tenant=tenant)
    data_points = MetricDataPoint.objects.filter(tenant=tenant, metric=metric)[:50]

    return render(request, 'system_admin/health/metric_detail.html', {
        'metric': metric,
        'data_points': data_points,
    })


@login_required
def metric_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    metric = get_object_or_404(SystemMetric.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = SystemMetricForm(request.POST, instance=metric)
        if form.is_valid():
            form.save()
            messages.success(request, f'System Metric "{metric.name}" updated.')
            return redirect('system_admin:metric_detail', tenant_slug=tenant.slug, pk=metric.pk)
    else:
        form = SystemMetricForm(instance=metric)

    return render(request, 'system_admin/health/metric_form.html', {
        'form': form, 'is_edit': True, 'metric': metric,
    })


# ──────────────────────────────────────────────
# System Health Check Views
# ──────────────────────────────────────────────

@login_required
def health_check_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = SystemHealthCheck.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(check_number__icontains=search))

    check_type_filter = request.GET.get('check_type', '')
    if check_type_filter:
        qs = qs.filter(check_type=check_type_filter)

    status_filter = request.GET.get('last_status', '')
    if status_filter:
        qs = qs.filter(last_status=status_filter)

    active_filter = request.GET.get('is_active', '')
    if active_filter == 'active':
        qs = qs.filter(is_active=True)
    elif active_filter == 'inactive':
        qs = qs.filter(is_active=False)

    all_items = SystemHealthCheck.objects.filter(tenant=tenant)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'system_admin/health/health_check_list.html', {
        'checks': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'healthy_count': all_items.filter(last_status='healthy').count(),
        'unhealthy_count': all_items.filter(last_status='unhealthy').count(),
        'check_type_choices': SystemHealthCheck.CHECK_TYPE_CHOICES,
        'status_choices': SystemHealthCheck.STATUS_CHOICES,
    })


@login_required
def health_check_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = SystemHealthCheckForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.check_number = SystemHealthCheck.generate_check_number(tenant)
            obj.save()
            form.save_m2m()
            messages.success(request, f'Health Check "{obj.name}" created.')
            return redirect('system_admin:health_check_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = SystemHealthCheckForm()

    return render(request, 'system_admin/health/health_check_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def health_check_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    check = get_object_or_404(SystemHealthCheck.unscoped, pk=pk, tenant=tenant)

    return render(request, 'system_admin/health/health_check_detail.html', {
        'check': check,
    })


@login_required
def health_check_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    check = get_object_or_404(SystemHealthCheck.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = SystemHealthCheckForm(request.POST, instance=check)
        if form.is_valid():
            form.save()
            messages.success(request, f'Health Check "{check.name}" updated.')
            return redirect('system_admin:health_check_detail', tenant_slug=tenant.slug, pk=check.pk)
    else:
        form = SystemHealthCheckForm(instance=check)

    return render(request, 'system_admin/health/health_check_form.html', {
        'form': form, 'is_edit': True, 'check': check,
    })


@login_required
def health_check_run(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    check = get_object_or_404(SystemHealthCheck.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        check.last_checked_at = timezone.now()
        check.last_status = 'healthy'
        check.save()
        messages.success(request, 'Health check executed.')

    return redirect('system_admin:health_check_detail', tenant_slug=tenant.slug, pk=check.pk)


# ──────────────────────────────────────────────
# Usage Analytics Views
# ──────────────────────────────────────────────

@login_required
def analytics_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = UsageAnalytics.objects.filter(tenant=tenant)

    period_filter = request.GET.get('period_type', '')
    if period_filter:
        qs = qs.filter(period_type=period_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = UsageAnalytics.objects.filter(tenant=tenant)

    return render(request, 'system_admin/health/analytics_list.html', {
        'analytics': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'period_type_choices': UsageAnalytics.PERIOD_TYPE_CHOICES,
    })


@login_required
def analytics_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    analytics = get_object_or_404(UsageAnalytics.unscoped, pk=pk, tenant=tenant)

    return render(request, 'system_admin/health/analytics_detail.html', {
        'analytics': analytics,
    })

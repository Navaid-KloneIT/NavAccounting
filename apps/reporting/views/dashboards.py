from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import ReportDashboardForm, DashboardWidgetFormSet, DashboardSnapshotForm
from ..models import ReportDashboard


@login_required
def dashboard_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ReportDashboard.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search))

    # Visibility filter
    visibility = request.GET.get('visibility', '')
    if visibility:
        qs = qs.filter(visibility=visibility)

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/dashboards/dashboard_list.html', {
        'dashboards': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'visibility_choices': ReportDashboard.VISIBILITY_CHOICES,
    })


@login_required
def dashboard_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ReportDashboardForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Dashboard "{obj.name}" created.')
            return redirect('reporting:dashboard_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = ReportDashboardForm()

    return render(request, 'reporting/dashboards/dashboard_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def dashboard_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    dashboard = get_object_or_404(ReportDashboard, pk=pk, tenant=tenant)
    widgets = dashboard.widgets.all()
    snapshots = dashboard.snapshots.all()[:10]

    return render(request, 'reporting/dashboards/dashboard_detail.html', {
        'dashboard': dashboard,
        'widgets': widgets,
        'snapshots': snapshots,
    })


@login_required
def dashboard_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    dashboard = get_object_or_404(ReportDashboard, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ReportDashboardForm(request.POST, instance=dashboard)
        widget_formset = DashboardWidgetFormSet(request.POST, instance=dashboard)
        if form.is_valid() and widget_formset.is_valid():
            form.save()
            widgets = widget_formset.save(commit=False)
            for w in widgets:
                w.tenant = tenant
                w.save()
            for w in widget_formset.deleted_objects:
                w.delete()
            messages.success(request, f'Dashboard "{dashboard.name}" updated.')
            return redirect('reporting:dashboard_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = ReportDashboardForm(instance=dashboard)
        widget_formset = DashboardWidgetFormSet(instance=dashboard)

    return render(request, 'reporting/dashboards/dashboard_form.html', {
        'form': form,
        'widget_formset': widget_formset,
        'dashboard': dashboard,
        'is_create': False,
    })


@login_required
def snapshot_create(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    dashboard = get_object_or_404(ReportDashboard, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = DashboardSnapshotForm(request.POST)
        if form.is_valid():
            snapshot = form.save(commit=False)
            snapshot.tenant = tenant
            snapshot.dashboard = dashboard
            snapshot.created_by = request.user
            snapshot.save()
            messages.success(request, f'Snapshot "{snapshot.snapshot_name}" created.')
            return redirect('reporting:dashboard_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = DashboardSnapshotForm()

    return render(request, 'reporting/dashboards/snapshot_form.html', {
        'form': form,
        'dashboard': dashboard,
    })

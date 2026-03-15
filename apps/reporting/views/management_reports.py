from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import ManagementReportForm, ManagementReportLineFormSet
from ..models import ManagementReport


@login_required
def report_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ManagementReport.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    distributed_count = qs.filter(status='distributed').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(report_number__icontains=search) | Q(name__icontains=search) |
            Q(department__icontains=search)
        )

    # Type filter
    report_type = request.GET.get('type', '')
    if report_type:
        qs = qs.filter(report_type=report_type)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/management_reports/report_list.html', {
        'reports': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'distributed_count': distributed_count,
        'type_choices': ManagementReport.REPORT_TYPE_CHOICES,
        'status_choices': ManagementReport.STATUS_CHOICES,
    })


@login_required
def report_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ManagementReportForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Management report "{obj.report_number}" created.')
            return redirect('reporting:mgmt_report_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = ManagementReportForm(tenant=tenant)

    return render(request, 'reporting/management_reports/report_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def report_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(ManagementReport, pk=pk, tenant=tenant)
    lines = report.lines.all()

    return render(request, 'reporting/management_reports/report_detail.html', {
        'report': report,
        'lines': lines,
    })


@login_required
def report_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(ManagementReport, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ManagementReportForm(request.POST, instance=report, tenant=tenant)
        line_formset = ManagementReportLineFormSet(request.POST, instance=report)
        if form.is_valid() and line_formset.is_valid():
            form.save()
            lines = line_formset.save(commit=False)
            for line in lines:
                line.tenant = tenant
                line.save()
            for line in line_formset.deleted_objects:
                line.delete()
            messages.success(request, f'Report "{report.report_number}" updated.')
            return redirect('reporting:mgmt_report_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = ManagementReportForm(instance=report, tenant=tenant)
        line_formset = ManagementReportLineFormSet(instance=report)

    return render(request, 'reporting/management_reports/report_form.html', {
        'form': form,
        'line_formset': line_formset,
        'report': report,
        'is_create': False,
    })


@login_required
def report_generate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(ManagementReport, pk=pk, tenant=tenant)
    if report.status == 'draft':
        report.status = 'generated'
        report.generated_at = timezone.now()
        report.generated_by = request.user
        report.save()
        messages.success(request, f'Report "{report.report_number}" generated.')
    else:
        messages.warning(request, 'Report can only be generated from draft status.')

    return redirect('reporting:mgmt_report_detail', tenant_slug=tenant.slug, pk=pk)

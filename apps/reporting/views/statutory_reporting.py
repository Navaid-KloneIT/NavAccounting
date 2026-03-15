from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import (
    StatutoryTemplateForm, StatutoryReportForm, StatutoryReportLineFormSet,
)
from ..models import StatutoryTemplate, StatutoryReport


# =============================================================================
# Statutory Templates
# =============================================================================

@login_required
def template_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = StatutoryTemplate.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(template_code__icontains=search) | Q(name__icontains=search) |
            Q(country__icontains=search)
        )

    # Framework filter
    framework = request.GET.get('framework', '')
    if framework:
        qs = qs.filter(framework=framework)

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/statutory_reporting/template_list.html', {
        'templates': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'framework_choices': StatutoryTemplate.FRAMEWORK_CHOICES,
    })


@login_required
def template_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = StatutoryTemplateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Template "{obj.template_code}" created.')
            return redirect('reporting:statutory_template_list', tenant_slug=tenant.slug)
    else:
        form = StatutoryTemplateForm()

    return render(request, 'reporting/statutory_reporting/template_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def template_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    template = get_object_or_404(StatutoryTemplate, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = StatutoryTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.template_code}" updated.')
            return redirect('reporting:statutory_template_list', tenant_slug=tenant.slug)
    else:
        form = StatutoryTemplateForm(instance=template)

    return render(request, 'reporting/statutory_reporting/template_form.html', {
        'form': form,
        'template': template,
        'is_create': False,
    })


# =============================================================================
# Statutory Reports
# =============================================================================

@login_required
def statutory_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = StatutoryReport.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    filed_count = qs.filter(status='filed').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(report_number__icontains=search) | Q(name__icontains=search)
        )

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/statutory_reporting/statutory_list.html', {
        'reports': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'filed_count': filed_count,
        'status_choices': StatutoryReport.STATUS_CHOICES,
    })


@login_required
def statutory_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = StatutoryReportForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, f'Statutory report "{obj.report_number}" created.')
            return redirect('reporting:statutory_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = StatutoryReportForm(tenant=tenant)

    return render(request, 'reporting/statutory_reporting/statutory_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def statutory_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(StatutoryReport, pk=pk, tenant=tenant)
    lines = report.lines.all()

    return render(request, 'reporting/statutory_reporting/statutory_detail.html', {
        'report': report,
        'lines': lines,
    })


@login_required
def statutory_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(StatutoryReport, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = StatutoryReportForm(request.POST, instance=report, tenant=tenant)
        line_formset = StatutoryReportLineFormSet(request.POST, instance=report)
        if form.is_valid() and line_formset.is_valid():
            form.save()
            lines = line_formset.save(commit=False)
            for line in lines:
                line.tenant = tenant
                line.save()
            for line in line_formset.deleted_objects:
                line.delete()
            messages.success(request, f'Report "{report.report_number}" updated.')
            return redirect('reporting:statutory_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = StatutoryReportForm(instance=report, tenant=tenant)
        line_formset = StatutoryReportLineFormSet(instance=report)

    return render(request, 'reporting/statutory_reporting/statutory_form.html', {
        'form': form,
        'line_formset': line_formset,
        'report': report,
        'is_create': False,
    })


@login_required
def statutory_generate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(StatutoryReport, pk=pk, tenant=tenant)
    if report.status == 'draft':
        report.status = 'generated'
        report.generated_at = timezone.now()
        report.generated_by = request.user
        report.save()
        messages.success(request, f'Report "{report.report_number}" generated.')
    else:
        messages.warning(request, 'Report can only be generated from draft status.')

    return redirect('reporting:statutory_detail', tenant_slug=tenant.slug, pk=pk)

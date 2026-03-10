from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import LocalGAAPAdjustmentForm, RegulatoryReportForm
from ..models import Entity, LocalGAAPAdjustment, RegulatoryReport


# =============================================================================
# Local GAAP Adjustments
# =============================================================================

@login_required
def gaap_adjustment_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = LocalGAAPAdjustment.objects.filter(tenant=tenant).select_related(
        'entity', 'fiscal_period', 'debit_account', 'credit_account'
    )

    total_count = qs.count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(adjustment_number__icontains=search) | Q(description__icontains=search)
        )

    # Entity filter
    entity_id = request.GET.get('entity', '')
    if entity_id:
        qs = qs.filter(entity_id=entity_id)

    # Type filter
    adj_type = request.GET.get('type', '')
    if adj_type:
        qs = qs.filter(adjustment_type=adj_type)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    entities = Entity.unscoped.filter(tenant=tenant, status='active')

    return render(request, 'multi_entity/regulatory/gaap_adjustment_list.html', {
        'adjustments': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'entities': entities,
        'type_choices': LocalGAAPAdjustment.ADJUSTMENT_TYPE_CHOICES,
        'status_choices': LocalGAAPAdjustment.STATUS_CHOICES,
    })


@login_required
def gaap_adjustment_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = LocalGAAPAdjustmentForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.adjustment_number = LocalGAAPAdjustment.generate_adjustment_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'GAAP Adjustment {obj.adjustment_number} created.')
            return redirect('multi_entity:gaap_adjustment_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = LocalGAAPAdjustmentForm(tenant=tenant)

    return render(request, 'multi_entity/regulatory/gaap_adjustment_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def gaap_adjustment_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    adj = get_object_or_404(
        LocalGAAPAdjustment.unscoped.select_related(
            'entity', 'fiscal_period', 'debit_account', 'credit_account',
            'journal_entry', 'created_by'
        ),
        pk=pk, tenant=tenant
    )

    return render(request, 'multi_entity/regulatory/gaap_adjustment_detail.html', {
        'adj': adj,
    })


@login_required
def gaap_adjustment_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    adj = get_object_or_404(LocalGAAPAdjustment.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and adj.status in ('draft', 'reviewed'):
        from ..services import post_gaap_adjustment
        try:
            post_gaap_adjustment(adj, tenant, request.user)
            messages.success(request, f'GAAP Adjustment {adj.adjustment_number} posted.')
        except Exception as e:
            messages.error(request, f'Error posting adjustment: {e}')

    return redirect('multi_entity:gaap_adjustment_detail', tenant_slug=tenant.slug, pk=pk)


# =============================================================================
# Regulatory Reports
# =============================================================================

@login_required
def regulatory_report_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = RegulatoryReport.objects.filter(tenant=tenant).select_related(
        'entity', 'fiscal_period'
    )

    total_count = qs.count()

    # Entity filter
    entity_id = request.GET.get('entity', '')
    if entity_id:
        qs = qs.filter(entity_id=entity_id)

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

    entities = Entity.unscoped.filter(tenant=tenant, status='active')

    return render(request, 'multi_entity/regulatory/regulatory_report_list.html', {
        'reports': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'entities': entities,
        'type_choices': RegulatoryReport.REPORT_TYPE_CHOICES,
        'status_choices': RegulatoryReport.STATUS_CHOICES,
    })


@login_required
def regulatory_report_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = RegulatoryReportForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.report_number = RegulatoryReport.generate_report_number(tenant)
            obj.generated_by = request.user
            obj.generated_at = timezone.now()
            obj.status = 'generated'
            obj.save()
            messages.success(request, f'Report {obj.report_number} generated.')
            return redirect('multi_entity:regulatory_report_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = RegulatoryReportForm(tenant=tenant)

    return render(request, 'multi_entity/regulatory/regulatory_report_form.html', {
        'form': form,
    })


@login_required
def regulatory_report_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(
        RegulatoryReport.unscoped.select_related(
            'entity', 'fiscal_period', 'generated_by'
        ),
        pk=pk, tenant=tenant
    )

    return render(request, 'multi_entity/regulatory/regulatory_report_detail.html', {
        'report': report,
    })


@login_required
def regulatory_report_file(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(RegulatoryReport.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST' and report.status in ('generated', 'reviewed'):
        report.status = 'filed'
        report.filed_at = timezone.now()
        report.filing_reference = request.POST.get('filing_reference', '')
        report.save()
        messages.success(request, f'Report {report.report_number} marked as filed.')

    return redirect('multi_entity:regulatory_report_detail', tenant_slug=tenant.slug, pk=pk)

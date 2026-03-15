from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import CustomReportForm, ReportColumnFormSet, ReportFilterFormSet
from ..models import CustomReport


@login_required
def builder_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = CustomReport.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()
    public_count = qs.filter(is_public=True).count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(report_code__icontains=search) | Q(name__icontains=search)
        )

    # Entity filter
    base_entity = request.GET.get('entity', '')
    if base_entity:
        qs = qs.filter(base_entity=base_entity)

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/report_builder/builder_list.html', {
        'reports': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'public_count': public_count,
        'entity_choices': CustomReport.BASE_ENTITY_CHOICES,
    })


@login_required
def builder_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CustomReportForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Custom report "{obj.report_code}" created.')
            return redirect('reporting:builder_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = CustomReportForm()

    return render(request, 'reporting/report_builder/builder_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def builder_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(CustomReport, pk=pk, tenant=tenant)
    columns = report.columns.all()
    filters = report.filters.all()

    return render(request, 'reporting/report_builder/builder_detail.html', {
        'report': report,
        'columns': columns,
        'filters': filters,
    })


@login_required
def builder_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    report = get_object_or_404(CustomReport, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = CustomReportForm(request.POST, instance=report)
        column_formset = ReportColumnFormSet(request.POST, instance=report, prefix='columns')
        filter_formset = ReportFilterFormSet(request.POST, instance=report, prefix='filters')
        if form.is_valid() and column_formset.is_valid() and filter_formset.is_valid():
            form.save()
            cols = column_formset.save(commit=False)
            for col in cols:
                col.tenant = tenant
                col.save()
            for col in column_formset.deleted_objects:
                col.delete()
            flts = filter_formset.save(commit=False)
            for flt in flts:
                flt.tenant = tenant
                flt.save()
            for flt in filter_formset.deleted_objects:
                flt.delete()
            messages.success(request, f'Report "{report.report_code}" updated.')
            return redirect('reporting:builder_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = CustomReportForm(instance=report)
        column_formset = ReportColumnFormSet(instance=report, prefix='columns')
        filter_formset = ReportFilterFormSet(instance=report, prefix='filters')

    return render(request, 'reporting/report_builder/builder_form.html', {
        'form': form,
        'column_formset': column_formset,
        'filter_formset': filter_formset,
        'report': report,
        'is_create': False,
    })

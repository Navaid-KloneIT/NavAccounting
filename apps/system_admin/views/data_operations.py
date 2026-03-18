from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import DataImportJobForm, DataExportJobForm, DataImportTemplateForm
from ..models import DataImportJob, DataExportJob, DataImportTemplate


# ──────────────────────────────────────────────
# Data Import Views
# ──────────────────────────────────────────────

@login_required
def import_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = DataImportJob.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(job_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    format_filter = request.GET.get('file_format', '')
    if format_filter:
        qs = qs.filter(file_format=format_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = DataImportJob.objects.filter(tenant=tenant)
    return render(request, 'system_admin/data_operations/import_list.html', {
        'imports': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'completed_count': all_items.filter(status='completed').count(),
        'failed_count': all_items.filter(status='failed').count(),
        'status_choices': DataImportJob.STATUS_CHOICES,
        'format_choices': DataImportJob.FILE_FORMAT_CHOICES,
    })


@login_required
def import_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = DataImportJobForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.job_number = DataImportJob.generate_job_number(tenant)
            obj.started_by = request.user
            if obj.source_file:
                obj.source_file_name = obj.source_file.name
            obj.save()
            form.save_m2m()
            messages.success(request, f'Import job "{obj.name}" created.')
            return redirect('system_admin:import_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = DataImportJobForm()

    return render(request, 'system_admin/data_operations/import_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def import_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    import_job = get_object_or_404(DataImportJob.unscoped, pk=pk, tenant=tenant)
    return render(request, 'system_admin/data_operations/import_detail.html', {
        'import_job': import_job,
    })


@login_required
def import_validate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('system_admin:import_detail', tenant_slug=tenant.slug, pk=pk)

    import_job = get_object_or_404(DataImportJob.unscoped, pk=pk, tenant=tenant)
    import_job.status = 'validating'
    import_job.save()
    messages.success(request, f'Import job "{import_job.name}" is now validating.')
    return redirect('system_admin:import_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def import_execute(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('system_admin:import_detail', tenant_slug=tenant.slug, pk=pk)

    import_job = get_object_or_404(DataImportJob.unscoped, pk=pk, tenant=tenant)
    import_job.status = 'importing'
    import_job.save()
    messages.success(request, f'Import job "{import_job.name}" is now importing.')
    return redirect('system_admin:import_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def import_cancel(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('system_admin:import_detail', tenant_slug=tenant.slug, pk=pk)

    import_job = get_object_or_404(DataImportJob.unscoped, pk=pk, tenant=tenant)
    import_job.status = 'cancelled'
    import_job.save()
    messages.success(request, f'Import job "{import_job.name}" has been cancelled.')
    return redirect('system_admin:import_detail', tenant_slug=tenant.slug, pk=pk)


# ──────────────────────────────────────────────
# Data Export Views
# ──────────────────────────────────────────────

@login_required
def export_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = DataExportJob.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(job_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    format_filter = request.GET.get('file_format', '')
    if format_filter:
        qs = qs.filter(file_format=format_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = DataExportJob.objects.filter(tenant=tenant)
    return render(request, 'system_admin/data_operations/export_list.html', {
        'exports': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'completed_count': all_items.filter(status='completed').count(),
        'pending_count': all_items.filter(status='pending').count(),
        'status_choices': DataExportJob.STATUS_CHOICES,
        'format_choices': DataExportJob.FILE_FORMAT_CHOICES,
    })


@login_required
def export_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = DataExportJobForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.job_number = DataExportJob.generate_job_number(tenant)
            obj.started_by = request.user
            obj.save()
            form.save_m2m()
            messages.success(request, f'Export job "{obj.name}" created.')
            return redirect('system_admin:export_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = DataExportJobForm()

    return render(request, 'system_admin/data_operations/export_form.html', {
        'form': form,
    })


@login_required
def export_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    export_job = get_object_or_404(DataExportJob.unscoped, pk=pk, tenant=tenant)
    return render(request, 'system_admin/data_operations/export_detail.html', {
        'export_job': export_job,
    })


@login_required
def export_download(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    export_job = get_object_or_404(DataExportJob.unscoped, pk=pk, tenant=tenant)
    if not export_job.output_file:
        raise Http404("Export file not found.")
    return FileResponse(export_job.output_file.open('rb'), as_attachment=True,
                        filename=export_job.output_file_name or export_job.output_file.name)


# ──────────────────────────────────────────────
# Data Import Template Views
# ──────────────────────────────────────────────

@login_required
def template_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = DataImportTemplate.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(template_number__icontains=search))

    format_filter = request.GET.get('file_format', '')
    if format_filter:
        qs = qs.filter(file_format=format_filter)

    active_filter = request.GET.get('is_active', '')
    if active_filter == 'active':
        qs = qs.filter(is_active=True)
    elif active_filter == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = DataImportTemplate.objects.filter(tenant=tenant)
    return render(request, 'system_admin/data_operations/template_list.html', {
        'templates': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(is_active=True).count(),
        'format_choices': DataImportTemplate.FILE_FORMAT_CHOICES,
    })


@login_required
def template_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = DataImportTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.template_number = DataImportTemplate.generate_template_number(tenant)
            obj.created_by = request.user
            obj.save()
            form.save_m2m()
            messages.success(request, f'Import template "{obj.name}" created.')
            return redirect('system_admin:import_template_list', tenant_slug=tenant.slug)
    else:
        form = DataImportTemplateForm()

    return render(request, 'system_admin/data_operations/template_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def template_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    template = get_object_or_404(DataImportTemplate.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = DataImportTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Import template "{template.name}" updated.')
            return redirect('system_admin:import_template_list', tenant_slug=tenant.slug)
    else:
        form = DataImportTemplateForm(instance=template)

    return render(request, 'system_admin/data_operations/template_form.html', {
        'form': form, 'is_edit': True, 'template': template,
    })


@login_required
def template_download_sample(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    template = get_object_or_404(DataImportTemplate.unscoped, pk=pk, tenant=tenant)
    if not template.sample_file:
        raise Http404("Sample file not found.")
    return FileResponse(template.sample_file.open('rb'), as_attachment=True,
                        filename=template.name + '_sample' or template.sample_file.name)

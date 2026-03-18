from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import BackupScheduleForm, BackupJobManualForm, RestoreJobForm
from ..models import BackupSchedule, BackupJob, RestoreJob


# ──────────────────────────────────────────────
# Backup Schedule Views
# ──────────────────────────────────────────────

@login_required
def schedule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = BackupSchedule.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(schedule_number__icontains=search) | Q(name__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    frequency_filter = request.GET.get('frequency', '')
    if frequency_filter:
        qs = qs.filter(frequency=frequency_filter)

    backup_type_filter = request.GET.get('backup_type', '')
    if backup_type_filter:
        qs = qs.filter(backup_type=backup_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = BackupSchedule.objects.filter(tenant=tenant)
    return render(request, 'system_admin/backups/schedule_list.html', {
        'schedules': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'active_count': all_items.filter(status='active').count(),
        'paused_count': all_items.filter(status='paused').count(),
        'status_choices': BackupSchedule.STATUS_CHOICES,
        'frequency_choices': BackupSchedule.FREQUENCY_CHOICES,
        'backup_type_choices': BackupSchedule.BACKUP_TYPE_CHOICES,
    })


@login_required
def schedule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BackupScheduleForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.schedule_number = BackupSchedule.generate_schedule_number(tenant)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Backup Schedule "{obj.name}" created.')
            return redirect('system_admin:backup_schedule_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = BackupScheduleForm()

    return render(request, 'system_admin/backups/schedule_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def schedule_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    schedule = get_object_or_404(BackupSchedule.unscoped, pk=pk, tenant=tenant)
    recent_jobs = BackupJob.objects.filter(tenant=tenant, schedule=schedule).order_by('-created_at')[:10]

    return render(request, 'system_admin/backups/schedule_detail.html', {
        'schedule': schedule,
        'recent_jobs': recent_jobs,
    })


@login_required
def schedule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    schedule = get_object_or_404(BackupSchedule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BackupScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Backup Schedule "{schedule.name}" updated.')
            return redirect('system_admin:backup_schedule_detail', tenant_slug=tenant.slug, pk=schedule.pk)
    else:
        form = BackupScheduleForm(instance=schedule)

    return render(request, 'system_admin/backups/schedule_form.html', {
        'form': form, 'is_edit': True, 'schedule': schedule,
    })


# ──────────────────────────────────────────────
# Backup Job Views
# ──────────────────────────────────────────────

@login_required
def job_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = BackupJob.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(job_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    backup_type_filter = request.GET.get('backup_type', '')
    if backup_type_filter:
        qs = qs.filter(backup_type=backup_type_filter)

    trigger_filter = request.GET.get('trigger', '')
    if trigger_filter:
        qs = qs.filter(trigger=trigger_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = BackupJob.objects.filter(tenant=tenant)
    return render(request, 'system_admin/backups/job_list.html', {
        'jobs': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'completed_count': all_items.filter(status='completed').count(),
        'failed_count': all_items.filter(status='failed').count(),
        'running_count': all_items.filter(status='running').count(),
        'status_choices': BackupJob.STATUS_CHOICES,
        'backup_type_choices': BackupJob.BACKUP_TYPE_CHOICES,
        'trigger_choices': BackupJob.TRIGGER_CHOICES,
    })


@login_required
def job_create_manual(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BackupJobManualForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.job_number = BackupJob.generate_job_number(tenant)
            obj.trigger = 'manual'
            obj.initiated_by = request.user
            obj.save()
            messages.success(request, f'Manual backup job "{obj.job_number}" created.')
            return redirect('system_admin:backup_job_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = BackupJobManualForm()

    return render(request, 'system_admin/backups/job_form.html', {
        'form': form,
    })


@login_required
def job_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    job = get_object_or_404(BackupJob.unscoped, pk=pk, tenant=tenant)
    restores = RestoreJob.objects.filter(tenant=tenant, backup=job).order_by('-created_at')[:10]

    return render(request, 'system_admin/backups/job_detail.html', {
        'job': job,
        'restores': restores,
    })


# ──────────────────────────────────────────────
# Restore Job Views
# ──────────────────────────────────────────────

@login_required
def restore_create(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    backup = get_object_or_404(BackupJob.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = RestoreJobForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.job_number = RestoreJob.generate_job_number(tenant)
            obj.backup = backup
            obj.initiated_by = request.user
            obj.save()
            messages.success(request, f'Restore job "{obj.job_number}" created.')
            return redirect('system_admin:restore_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = RestoreJobForm()

    return render(request, 'system_admin/backups/restore_form.html', {
        'form': form, 'backup': backup,
    })


@login_required
def restore_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = RestoreJob.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(job_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    restore_type_filter = request.GET.get('restore_type', '')
    if restore_type_filter:
        qs = qs.filter(restore_type=restore_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_items = RestoreJob.objects.filter(tenant=tenant)
    return render(request, 'system_admin/backups/restore_list.html', {
        'restores': page_obj,
        'page_obj': page_obj,
        'total_count': all_items.count(),
        'completed_count': all_items.filter(status='completed').count(),
        'failed_count': all_items.filter(status='failed').count(),
        'status_choices': RestoreJob.STATUS_CHOICES,
        'restore_type_choices': RestoreJob.RESTORE_TYPE_CHOICES,
    })


@login_required
def restore_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    restore = get_object_or_404(RestoreJob.unscoped, pk=pk, tenant=tenant)

    return render(request, 'system_admin/backups/restore_detail.html', {
        'restore': restore,
    })

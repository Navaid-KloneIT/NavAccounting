from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import ReportScheduleForm, ScheduleRecipientFormSet
from ..models import ReportSchedule


@login_required
def schedule_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ReportSchedule.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    active_count = qs.filter(status='active').count()
    paused_count = qs.filter(status='paused').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(schedule_name__icontains=search))

    # Frequency filter
    frequency = request.GET.get('frequency', '')
    if frequency:
        qs = qs.filter(frequency=frequency)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/scheduled_reports/schedule_list.html', {
        'schedules': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'paused_count': paused_count,
        'frequency_choices': ReportSchedule.FREQUENCY_CHOICES,
        'status_choices': ReportSchedule.STATUS_CHOICES,
    })


@login_required
def schedule_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ReportScheduleForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Schedule "{obj.schedule_name}" created.')
            return redirect('reporting:schedule_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = ReportScheduleForm(tenant=tenant)

    return render(request, 'reporting/scheduled_reports/schedule_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def schedule_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    schedule = get_object_or_404(ReportSchedule, pk=pk, tenant=tenant)
    recipients = schedule.recipients.all()
    executions = schedule.executions.all()[:20]

    return render(request, 'reporting/scheduled_reports/schedule_detail.html', {
        'schedule': schedule,
        'recipients': recipients,
        'executions': executions,
    })


@login_required
def schedule_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    schedule = get_object_or_404(ReportSchedule, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ReportScheduleForm(request.POST, instance=schedule, tenant=tenant)
        recipient_formset = ScheduleRecipientFormSet(request.POST, instance=schedule)
        if form.is_valid() and recipient_formset.is_valid():
            form.save()
            recipients = recipient_formset.save(commit=False)
            for r in recipients:
                r.tenant = tenant
                r.save()
            for r in recipient_formset.deleted_objects:
                r.delete()
            messages.success(request, f'Schedule "{schedule.schedule_name}" updated.')
            return redirect('reporting:schedule_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = ReportScheduleForm(instance=schedule, tenant=tenant)
        recipient_formset = ScheduleRecipientFormSet(instance=schedule)

    return render(request, 'reporting/scheduled_reports/schedule_form.html', {
        'form': form,
        'recipient_formset': recipient_formset,
        'schedule': schedule,
        'is_create': False,
    })

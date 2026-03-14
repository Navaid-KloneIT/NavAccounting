from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import TaxDeadlineForm
from ..models import TaxDeadline


@login_required
def deadline_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    # Check and mark overdue deadlines
    from ..services import check_overdue_deadlines
    check_overdue_deadlines(tenant)

    qs = TaxDeadline.objects.filter(tenant=tenant).select_related('jurisdiction')

    total_count = qs.count()
    upcoming_count = qs.filter(status='upcoming').count()
    overdue_count = qs.filter(status='overdue').count()
    filed_count = qs.filter(status='filed').count()

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(deadline_number__icontains=search) | Q(name__icontains=search)
        )

    tax_type = request.GET.get('tax_type', '')
    if tax_type:
        qs = qs.filter(tax_type=tax_type)

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tax/calendar/deadline_list.html', {
        'deadlines': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'upcoming_count': upcoming_count,
        'overdue_count': overdue_count,
        'filed_count': filed_count,
        'tax_type_choices': TaxDeadline.TAX_TYPE_CHOICES,
        'status_choices': TaxDeadline.STATUS_CHOICES,
    })


@login_required
def deadline_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = TaxDeadlineForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.deadline_number = TaxDeadline.generate_deadline_number(tenant)
            obj.save()
            messages.success(request, f'Deadline "{obj.name}" created.')
            return redirect('tax:deadline_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = TaxDeadlineForm(tenant=tenant)

    return render(request, 'tax/calendar/deadline_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def deadline_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    deadline = get_object_or_404(TaxDeadline.unscoped, pk=pk, tenant=tenant)
    reminders = deadline.reminders.all()

    return render(request, 'tax/calendar/deadline_detail.html', {
        'deadline': deadline,
        'reminders': reminders,
    })


@login_required
def deadline_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    deadline = get_object_or_404(TaxDeadline.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TaxDeadlineForm(request.POST, instance=deadline, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Deadline "{deadline.name}" updated.')
            return redirect('tax:deadline_detail', tenant_slug=tenant.slug, pk=deadline.pk)
    else:
        form = TaxDeadlineForm(instance=deadline, tenant=tenant)

    return render(request, 'tax/calendar/deadline_form.html', {
        'form': form, 'is_edit': True, 'deadline': deadline,
    })


@login_required
def deadline_complete(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    deadline = get_object_or_404(TaxDeadline.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        deadline.status = 'filed'
        deadline.save()
        messages.success(request, f'Deadline "{deadline.name}" marked as filed.')

    return redirect('tax:deadline_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def generate_recurring(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        from_date_str = request.POST.get('from_date', '')
        to_date_str = request.POST.get('to_date', '')

        if from_date_str and to_date_str:
            from datetime import date
            try:
                from_date = date.fromisoformat(from_date_str)
                to_date = date.fromisoformat(to_date_str)
                from ..services import generate_recurring_deadlines
                created = generate_recurring_deadlines(tenant, from_date, to_date)
                messages.success(request, f'{len(created)} recurring deadlines generated.')
            except (ValueError, ImportError):
                messages.error(request, 'Invalid date format or missing dateutil library.')
        else:
            messages.error(request, 'Both from and to dates are required.')

        return redirect('tax:deadline_list', tenant_slug=tenant.slug)

    return render(request, 'tax/calendar/generate_form.html', {})

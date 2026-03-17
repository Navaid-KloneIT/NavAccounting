from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant
from ..forms import ChangeRequestForm, ChangeApprovalFormSet
from ..models import ChangeRequest, ChangeApproval
from ..services import process_change_approval


@login_required
def change_request_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = ChangeRequest.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(request_number__icontains=search) |
            Q(title__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        qs = qs.filter(priority=priority_filter)

    change_type_filter = request.GET.get('change_type', '')
    if change_type_filter:
        qs = qs.filter(change_type=change_type_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_requests = ChangeRequest.objects.filter(tenant=tenant)
    return render(request, 'audit/change_management/change_request_list.html', {
        'change_requests': page_obj,
        'page_obj': page_obj,
        'total_count': all_requests.count(),
        'submitted_count': all_requests.filter(status='submitted').count(),
        'approved_count': all_requests.filter(status='approved').count(),
        'status_choices': ChangeRequest.STATUS_CHOICES,
        'priority_choices': ChangeRequest.PRIORITY_CHOICES,
        'change_type_choices': ChangeRequest.CHANGE_TYPE_CHOICES,
    })


@login_required
def change_request_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ChangeRequestForm(request.POST)
        formset = ChangeApprovalFormSet(request.POST, prefix='approvals')
        if form.is_valid() and formset.is_valid():
            cr = form.save(commit=False)
            cr.tenant = tenant
            cr.request_number = ChangeRequest.generate_request_number(tenant)
            cr.requested_by = request.user
            cr.save()
            formset.instance = cr
            approvals = formset.save(commit=False)
            for approval in approvals:
                approval.tenant = tenant
                approval.approval_number = ChangeApproval.generate_approval_number(tenant)
                approval.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Change Request "{cr.title}" created.')
            return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=cr.pk)
    else:
        form = ChangeRequestForm()
        formset = ChangeApprovalFormSet(prefix='approvals')

    return render(request, 'audit/change_management/change_request_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def change_request_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    cr = get_object_or_404(ChangeRequest.unscoped, pk=pk, tenant=tenant)
    approvals = cr.approvals.select_related('approver').all()

    return render(request, 'audit/change_management/change_request_detail.html', {
        'cr': cr,
        'approvals': approvals,
    })


@login_required
def change_request_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    cr = get_object_or_404(ChangeRequest.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ChangeRequestForm(request.POST, instance=cr)
        formset = ChangeApprovalFormSet(
            request.POST, instance=cr, prefix='approvals',
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            approvals = formset.save(commit=False)
            for approval in approvals:
                approval.tenant = tenant
                if not approval.approval_number:
                    approval.approval_number = ChangeApproval.generate_approval_number(tenant)
                approval.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Change Request "{cr.title}" updated.')
            return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=cr.pk)
    else:
        form = ChangeRequestForm(instance=cr)
        formset = ChangeApprovalFormSet(instance=cr, prefix='approvals')

    return render(request, 'audit/change_management/change_request_form.html', {
        'form': form, 'formset': formset, 'is_edit': True, 'cr': cr,
    })


@login_required
def change_request_submit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=pk)

    cr = get_object_or_404(ChangeRequest.unscoped, pk=pk, tenant=tenant)
    if cr.status == 'draft':
        cr.status = 'submitted'
        cr.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Change Request "{cr.title}" submitted.')
    else:
        messages.warning(request, 'Change request can only be submitted from draft status.')
    return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=cr.pk)


@login_required
def change_request_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=pk)

    cr = get_object_or_404(ChangeRequest.unscoped, pk=pk, tenant=tenant)
    if cr.status in ['submitted', 'under_review']:
        cr.approved_by = request.user
        cr.approved_at = timezone.now()
        cr.status = 'approved'
        cr.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        messages.success(request, f'Change Request "{cr.title}" approved.')
    else:
        messages.warning(request, 'Change request can only be approved from submitted or under-review status.')
    return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=cr.pk)


@login_required
def change_request_reject(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=pk)

    cr = get_object_or_404(ChangeRequest.unscoped, pk=pk, tenant=tenant)
    if cr.status in ['submitted', 'under_review']:
        cr.status = 'rejected'
        cr.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Change Request "{cr.title}" rejected.')
    else:
        messages.warning(request, 'Change request can only be rejected from submitted or under-review status.')
    return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=cr.pk)


@login_required
def change_request_implement(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method != 'POST':
        return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=pk)

    cr = get_object_or_404(ChangeRequest.unscoped, pk=pk, tenant=tenant)
    if cr.status == 'approved':
        cr.implemented_by = request.user
        cr.implemented_at = timezone.now()
        cr.status = 'implemented'
        cr.save(update_fields=['status', 'implemented_by', 'implemented_at', 'updated_at'])
        messages.success(request, f'Change Request "{cr.title}" implemented.')
    else:
        messages.warning(request, 'Change request can only be implemented from approved status.')
    return redirect('audit:change_request_detail', tenant_slug=tenant.slug, pk=cr.pk)

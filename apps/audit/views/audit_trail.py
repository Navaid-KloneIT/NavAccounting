from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..models import AuditEntry


@login_required
def audit_entry_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = AuditEntry.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(entry_number__icontains=search) |
            Q(model_name__icontains=search) |
            Q(changes_summary__icontains=search)
        )

    action_filter = request.GET.get('action', '')
    if action_filter:
        qs = qs.filter(action=action_filter)

    date_from = request.GET.get('date_from', '')
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_entries = AuditEntry.objects.filter(tenant=tenant)
    return render(request, 'audit/audit_trail/audit_entry_list.html', {
        'entries': page_obj,
        'page_obj': page_obj,
        'total_count': all_entries.count(),
        'create_count': all_entries.filter(action='create').count(),
        'update_count': all_entries.filter(action='update').count(),
        'delete_count': all_entries.filter(action='delete').count(),
        'action_choices': AuditEntry.ACTION_CHOICES,
    })


@login_required
def audit_entry_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    entry = get_object_or_404(AuditEntry.unscoped, pk=pk, tenant=tenant)

    return render(request, 'audit/audit_trail/audit_entry_detail.html', {
        'entry': entry,
    })

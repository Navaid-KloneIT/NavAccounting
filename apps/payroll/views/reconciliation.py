from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import PayrollReconciliationForm
from ..models import PayrollReconciliation
from ..services import perform_reconciliation


@login_required
def reconciliation_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = PayrollReconciliation.objects.filter(tenant=tenant).select_related('payroll_journal')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(reconciliation_number__icontains=search) |
            Q(payroll_journal__journal_number__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/reconciliation/reconciliation_list.html', {
        'reconciliations': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def reconciliation_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PayrollReconciliationForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.reconciliation_number = PayrollReconciliation.generate_reconciliation_number(tenant)
            obj.reconciled_by = request.user
            obj.save()
            perform_reconciliation(obj, tenant)
            messages.success(request, f'Reconciliation "{obj.reconciliation_number}" completed.')
            return redirect('payroll:reconciliation_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = PayrollReconciliationForm(tenant=tenant)

    return render(request, 'payroll/reconciliation/reconciliation_form.html', {
        'form': form,
    })


@login_required
def reconciliation_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    recon = get_object_or_404(PayrollReconciliation.unscoped, pk=pk, tenant=tenant)

    return render(request, 'payroll/reconciliation/reconciliation_detail.html', {
        'recon': recon,
    })

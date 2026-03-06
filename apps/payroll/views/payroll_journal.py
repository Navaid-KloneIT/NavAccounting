from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant

from ..forms import PayrollJournalForm, PayrollJournalLineFormSet
from ..models import PayrollJournal, Employee
from ..services import calculate_payroll_journal, post_payroll_journal


@login_required
def journal_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = PayrollJournal.objects.filter(tenant=tenant)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(journal_number__icontains=search))

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'payroll/payroll_journal/journal_list.html', {
        'journals': page_obj,
        'page_obj': page_obj,
        'total_count': qs.count(),
    })


@login_required
def journal_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = PayrollJournalForm(request.POST, tenant=tenant)
        formset = PayrollJournalLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            journal = form.save(commit=False)
            journal.tenant = tenant
            journal.journal_number = PayrollJournal.generate_journal_number(tenant)
            journal.created_by = request.user
            journal.save()
            formset.instance = journal
            formset.save()
            messages.success(request, f'Payroll journal "{journal.journal_number}" created.')
            return redirect('payroll:journal_detail', tenant_slug=tenant.slug, pk=journal.pk)
    else:
        form = PayrollJournalForm(tenant=tenant)
        formset = PayrollJournalLineFormSet()
        # Filter employee choices in formset
        for f in formset.forms:
            f.fields['employee'].queryset = Employee.unscoped.filter(
                tenant=tenant, is_active=True
            )

    return render(request, 'payroll/payroll_journal/journal_form.html', {
        'form': form, 'formset': formset, 'is_edit': False,
    })


@login_required
def journal_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    journal = get_object_or_404(PayrollJournal.unscoped, pk=pk, tenant=tenant)
    lines = journal.lines.select_related('employee').all()

    return render(request, 'payroll/payroll_journal/journal_detail.html', {
        'journal': journal,
        'lines': lines,
    })


@login_required
def journal_calculate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    journal = get_object_or_404(PayrollJournal.unscoped, pk=pk, tenant=tenant)
    if journal.status not in ('draft', 'calculated'):
        messages.error(request, 'Only draft or calculated journals can be recalculated.')
        return redirect('payroll:journal_detail', tenant_slug=tenant.slug, pk=pk)

    calculate_payroll_journal(journal, tenant)
    messages.success(request, f'Payroll journal "{journal.journal_number}" calculated.')
    return redirect('payroll:journal_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def journal_approve(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    journal = get_object_or_404(PayrollJournal.unscoped, pk=pk, tenant=tenant)
    if journal.status != 'calculated':
        messages.error(request, 'Only calculated journals can be approved.')
        return redirect('payroll:journal_detail', tenant_slug=tenant.slug, pk=pk)

    journal.status = 'approved'
    journal.save()
    messages.success(request, f'Payroll journal "{journal.journal_number}" approved.')
    return redirect('payroll:journal_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def journal_post(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    journal = get_object_or_404(PayrollJournal.unscoped, pk=pk, tenant=tenant)
    if journal.status != 'approved':
        messages.error(request, 'Only approved journals can be posted.')
        return redirect('payroll:journal_detail', tenant_slug=tenant.slug, pk=pk)

    post_payroll_journal(journal, tenant, request.user)
    messages.success(request, f'Payroll journal "{journal.journal_number}" posted to GL.')
    return redirect('payroll:journal_detail', tenant_slug=tenant.slug, pk=pk)

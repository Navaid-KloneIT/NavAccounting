from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.company.models import (
    ChartOfAccountsTemplate, CompanySettings, FiscalPeriod,
)
from apps.tenants.managers import set_current_tenant

from .forms import (
    AccountForm, AccountReconciliationForm, AllocationRuleForm,
    AllocationRuleLineFormSet, ApprovalActionForm, ExchangeRateForm,
    JournalEntryForm, JournalEntryLineFormSet,
)
from .models import (
    Account, AccountReconciliation, AllocationRule, AuditTrail,
    ExchangeRate, JournalApproval, JournalEntry, JournalEntryLine,
    PeriodCloseChecklist,
)


# =============================================================================
# Chart of Accounts Views
# =============================================================================

@login_required
def account_list(request, tenant_slug):
    """List all chart of accounts entries in a tree view."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = Account.objects.filter(tenant=tenant).select_related('account_type', 'parent')

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()
    header_count = qs.filter(is_header=True).count()

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(account_number__icontains=search_query) |
            Q(name__icontains=search_query)
        )

    # Type filter
    type_filter = request.GET.get('type', '')
    if type_filter:
        qs = qs.filter(account_type_id=type_filter)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    # Build tree with level for indentation
    flat_accounts = list(qs)
    tree = _build_account_tree(flat_accounts)

    # Account types for filter dropdown
    from apps.company.models import AccountType
    account_types = AccountType.objects.all()

    return render(request, 'general_ledger/chart_of_accounts/account_list.html', {
        'accounts': tree,
        'total_count': total_count,
        'active_count': active_count,
        'header_count': header_count,
        'account_types': account_types,
    })


def _build_account_tree(accounts):
    """Build flat list with level attribute for tree indentation."""
    account_map = {a.pk: a for a in accounts}
    roots = []
    children_map = {}

    for a in accounts:
        if a.parent_id and a.parent_id in account_map:
            children_map.setdefault(a.parent_id, []).append(a)
        else:
            roots.append(a)

    result = []

    def _add(account, level):
        account.level = level
        result.append(account)
        for child in children_map.get(account.pk, []):
            _add(child, level + 1)

    for root in roots:
        _add(root, 0)

    return result


@login_required
def account_create(request, tenant_slug):
    """Create a new account."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AccountForm(request.POST, tenant=tenant)
        if form.is_valid():
            account = form.save(commit=False)
            account.tenant = tenant
            account._current_user = request.user
            account.save()
            messages.success(request, f'Account "{account}" created.')
            return redirect('general_ledger:account_list', tenant_slug=tenant_slug)
    else:
        form = AccountForm(tenant=tenant)

    return render(request, 'general_ledger/chart_of_accounts/account_form.html', {
        'form': form,
        'title': 'Create Account',
    })


@login_required
def account_edit(request, tenant_slug, pk):
    """Edit an existing account."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    account = get_object_or_404(Account, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj._current_user = request.user
            obj.save()
            messages.success(request, f'Account "{account}" updated.')
            return redirect('general_ledger:account_list', tenant_slug=tenant_slug)
    else:
        form = AccountForm(instance=account, tenant=tenant)

    return render(request, 'general_ledger/chart_of_accounts/account_form.html', {
        'form': form,
        'title': f'Edit: {account}',
    })


@login_required
def account_delete(request, tenant_slug, pk):
    """Soft-delete (deactivate) an account."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    account = get_object_or_404(Account, pk=pk, tenant=tenant)

    if request.method == 'POST':
        # Check if account has journal lines
        has_lines = JournalEntryLine.objects.filter(account=account).exists()
        if has_lines:
            messages.error(request, f'Cannot deactivate "{account}" — it has journal entry lines.')
        else:
            account.is_active = False
            account._current_user = request.user
            account.save()
            messages.success(request, f'Account "{account}" deactivated.')

    return redirect('general_ledger:account_list', tenant_slug=tenant_slug)


@login_required
def account_import_template(request, tenant_slug):
    """Import accounts from a COA template into tenant accounts."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    templates = ChartOfAccountsTemplate.objects.all().prefetch_related('items')

    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        template = get_object_or_404(ChartOfAccountsTemplate, pk=template_id)
        items = template.items.select_related('account_type', 'parent').order_by('display_order')

        # Map template item PKs to new Account PKs for parent resolution
        parent_map = {}
        created_count = 0

        for item in items:
            parent = parent_map.get(item.parent_id) if item.parent_id else None
            account, created = Account.unscoped.get_or_create(
                tenant=tenant,
                account_number=item.account_code,
                defaults={
                    'name': item.account_name,
                    'account_type': item.account_type,
                    'parent': parent,
                    'is_header': item.is_header,
                    'description': item.description,
                    'display_order': item.display_order,
                }
            )
            parent_map[item.pk] = account
            if created:
                created_count += 1

        messages.success(request, f'Imported {created_count} accounts from "{template.name}".')
        return redirect('general_ledger:account_list', tenant_slug=tenant_slug)

    return render(request, 'general_ledger/chart_of_accounts/import_template.html', {
        'templates': templates,
    })


# =============================================================================
# Journal Entry Views
# =============================================================================

@login_required
def journal_list(request, tenant_slug):
    """List all journal entries."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = JournalEntry.objects.filter(tenant=tenant).select_related(
        'fiscal_period', 'currency', 'created_by'
    )

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    pending_count = qs.filter(status='pending').count()
    posted_count = qs.filter(status='posted').count()

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(entry_number__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(reference__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Date filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'general_ledger/journal_entries/journal_list.html', {
        'journal_entries': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'pending_count': pending_count,
        'posted_count': posted_count,
    })


@login_required
def journal_create(request, tenant_slug):
    """Create a new journal entry with lines."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    # Default currency from company settings
    company_settings = CompanySettings.unscoped.filter(tenant=tenant).first()
    default_currency = company_settings.base_currency if company_settings else None

    if request.method == 'POST':
        form = JournalEntryForm(request.POST, tenant=tenant)
        formset = JournalEntryLineFormSet(request.POST, prefix='lines')

        # Set account queryset on each formset form
        for f in formset.forms:
            f.fields['account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

        if form.is_valid() and formset.is_valid():
            je = form.save(commit=False)
            je.tenant = tenant
            je.entry_number = JournalEntry.generate_entry_number(tenant)
            je.created_by = request.user
            je.status = 'draft'
            je._current_user = request.user
            je.save()

            formset.instance = je
            formset.save()

            # Validate balance
            if not je.is_balanced:
                messages.warning(request, 'Warning: Total debits do not equal total credits.')

            messages.success(request, f'Journal entry "{je.entry_number}" created.')
            return redirect('general_ledger:journal_detail', tenant_slug=tenant_slug, pk=je.pk)
    else:
        initial = {}
        if default_currency:
            initial['currency'] = default_currency.pk
        form = JournalEntryForm(tenant=tenant, initial=initial)
        formset = JournalEntryLineFormSet(prefix='lines')
        for f in formset.forms:
            f.fields['account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

    return render(request, 'general_ledger/journal_entries/journal_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Journal Entry',
    })


@login_required
def journal_detail(request, tenant_slug, pk):
    """View journal entry details."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    je = get_object_or_404(
        JournalEntry.objects.select_related('fiscal_period', 'currency', 'created_by', 'posted_by'),
        pk=pk, tenant=tenant
    )
    lines = je.lines.select_related('account', 'account__account_type')
    approvals = je.approvals.select_related('approver').all()

    return render(request, 'general_ledger/journal_entries/journal_detail.html', {
        'je': je,
        'lines': lines,
        'approvals': approvals,
    })


@login_required
def journal_edit(request, tenant_slug, pk):
    """Edit a draft journal entry."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    je = get_object_or_404(JournalEntry, pk=pk, tenant=tenant)

    if je.status != 'draft':
        messages.error(request, 'Only draft journal entries can be edited.')
        return redirect('general_ledger:journal_detail', tenant_slug=tenant_slug, pk=pk)

    if request.method == 'POST':
        form = JournalEntryForm(request.POST, instance=je, tenant=tenant)
        formset = JournalEntryLineFormSet(request.POST, instance=je, prefix='lines')

        for f in formset.forms:
            f.fields['account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj._current_user = request.user
            obj.save()
            formset.save()

            if not je.is_balanced:
                messages.warning(request, 'Warning: Total debits do not equal total credits.')

            messages.success(request, f'Journal entry "{je.entry_number}" updated.')
            return redirect('general_ledger:journal_detail', tenant_slug=tenant_slug, pk=pk)
    else:
        form = JournalEntryForm(instance=je, tenant=tenant)
        formset = JournalEntryLineFormSet(instance=je, prefix='lines')
        for f in formset.forms:
            f.fields['account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

    return render(request, 'general_ledger/journal_entries/journal_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {je.entry_number}',
        'je': je,
    })


@login_required
def journal_submit(request, tenant_slug, pk):
    """Submit a journal entry for approval."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    je = get_object_or_404(JournalEntry, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if je.status != 'draft':
            messages.error(request, 'Only draft entries can be submitted for approval.')
        elif not je.is_balanced:
            messages.error(request, 'Cannot submit: debits do not equal credits.')
        else:
            je.status = 'pending'
            je._current_user = request.user
            je.save()

            JournalApproval.objects.create(
                tenant=tenant,
                journal_entry=je,
                approver=request.user,
                status='pending',
            )
            messages.success(request, f'Journal entry "{je.entry_number}" submitted for approval.')

    return redirect('general_ledger:journal_detail', tenant_slug=tenant_slug, pk=pk)


@login_required
def journal_post(request, tenant_slug, pk):
    """Post an approved journal entry."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    je = get_object_or_404(JournalEntry, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if je.status != 'approved':
            messages.error(request, 'Only approved entries can be posted.')
        else:
            je.status = 'posted'
            je.posted_by = request.user
            je.posted_at = timezone.now()
            je._current_user = request.user
            je.save()
            messages.success(request, f'Journal entry "{je.entry_number}" has been posted.')

    return redirect('general_ledger:journal_detail', tenant_slug=tenant_slug, pk=pk)


# =============================================================================
# Journal Approval Views
# =============================================================================

@login_required
def approval_queue(request, tenant_slug):
    """List journal entries pending approval."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = JournalEntry.objects.filter(
        tenant=tenant, status='pending'
    ).select_related('fiscal_period', 'currency', 'created_by')

    pending_count = qs.count()

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'general_ledger/approvals/approval_queue.html', {
        'journal_entries': page_obj,
        'page_obj': page_obj,
        'pending_count': pending_count,
    })


@login_required
def approval_detail(request, tenant_slug, pk):
    """View journal entry for approval with action form."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    je = get_object_or_404(
        JournalEntry.objects.select_related('fiscal_period', 'currency', 'created_by'),
        pk=pk, tenant=tenant
    )
    lines = je.lines.select_related('account', 'account__account_type')
    approvals = je.approvals.select_related('approver').all()
    form = ApprovalActionForm()

    return render(request, 'general_ledger/approvals/approval_detail.html', {
        'je': je,
        'lines': lines,
        'approvals': approvals,
        'form': form,
    })


@login_required
def approval_approve(request, tenant_slug, pk):
    """Approve a journal entry."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    je = get_object_or_404(JournalEntry, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if je.status != 'pending':
            messages.error(request, 'Only pending entries can be approved.')
        else:
            comments = request.POST.get('comments', '')

            # Update or create approval record
            approval = je.approvals.filter(status='pending').first()
            if approval:
                approval.status = 'approved'
                approval.comments = comments
                approval.approved_at = timezone.now()
                approval.approver = request.user
                approval.save()
            else:
                JournalApproval.objects.create(
                    tenant=tenant,
                    journal_entry=je,
                    approver=request.user,
                    status='approved',
                    comments=comments,
                    approved_at=timezone.now(),
                )

            je.status = 'approved'
            je._current_user = request.user
            je.save()
            messages.success(request, f'Journal entry "{je.entry_number}" approved.')

    return redirect('general_ledger:approval_queue', tenant_slug=tenant_slug)


@login_required
def approval_reject(request, tenant_slug, pk):
    """Reject a journal entry."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    je = get_object_or_404(JournalEntry, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if je.status != 'pending':
            messages.error(request, 'Only pending entries can be rejected.')
        else:
            comments = request.POST.get('comments', '')

            approval = je.approvals.filter(status='pending').first()
            if approval:
                approval.status = 'rejected'
                approval.comments = comments
                approval.approved_at = timezone.now()
                approval.approver = request.user
                approval.save()
            else:
                JournalApproval.objects.create(
                    tenant=tenant,
                    journal_entry=je,
                    approver=request.user,
                    status='rejected',
                    comments=comments,
                    approved_at=timezone.now(),
                )

            je.status = 'rejected'
            je._current_user = request.user
            je.save()
            messages.success(request, f'Journal entry "{je.entry_number}" rejected.')

    return redirect('general_ledger:approval_queue', tenant_slug=tenant_slug)


# =============================================================================
# Period Close Views
# =============================================================================

@login_required
def period_close_list(request, tenant_slug):
    """List all fiscal periods with close status."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    periods = FiscalPeriod.objects.filter(tenant=tenant).select_related(
        'fiscal_year'
    ).prefetch_related('close_checklist')

    # Stats
    total_count = periods.count()
    open_count = periods.filter(is_closed=False).count()
    closed_count = periods.filter(is_closed=True).count()

    # Year filter
    year_filter = request.GET.get('year', '')
    if year_filter:
        periods = periods.filter(fiscal_year_id=year_filter)

    from apps.company.models import FiscalYear
    fiscal_years = FiscalYear.objects.filter(tenant=tenant)

    return render(request, 'general_ledger/period_close/period_close_list.html', {
        'periods': periods,
        'total_count': total_count,
        'open_count': open_count,
        'closed_count': closed_count,
        'fiscal_years': fiscal_years,
    })


@login_required
def period_close_detail(request, tenant_slug, pk):
    """View period close checklist and details."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    period = get_object_or_404(FiscalPeriod, pk=pk, tenant=tenant)

    # Create default checklist items if none exist
    default_steps = [
        (1, 'Review all journal entries'),
        (2, 'Post all pending entries'),
        (3, 'Verify account reconciliations'),
        (4, 'Review trial balance'),
        (5, 'Generate closing entries'),
    ]
    for order, name in default_steps:
        PeriodCloseChecklist.unscoped.get_or_create(
            tenant=tenant,
            fiscal_period=period,
            step_name=name,
            defaults={'step_order': order}
        )

    checklist = PeriodCloseChecklist.objects.filter(
        tenant=tenant, fiscal_period=period
    ).order_by('step_order')

    # Period stats
    unposted_count = JournalEntry.objects.filter(
        tenant=tenant, fiscal_period=period
    ).exclude(status='posted').count()
    posted_count = JournalEntry.objects.filter(
        tenant=tenant, fiscal_period=period, status='posted'
    ).count()
    completed_steps = checklist.filter(is_completed=True).count()
    total_steps = checklist.count()

    # Handle checklist item completion toggle
    if request.method == 'POST':
        step_id = request.POST.get('step_id')
        if step_id:
            step = get_object_or_404(PeriodCloseChecklist, pk=step_id, tenant=tenant)
            step.is_completed = not step.is_completed
            if step.is_completed:
                step.completed_by = request.user
                step.completed_at = timezone.now()
            else:
                step.completed_by = None
                step.completed_at = None
            step._current_user = request.user
            step.save()
            messages.success(request, f'Step "{step.step_name}" updated.')
            return redirect('general_ledger:period_close_detail', tenant_slug=tenant_slug, pk=pk)

    return render(request, 'general_ledger/period_close/period_close_detail.html', {
        'period': period,
        'checklist': checklist,
        'unposted_count': unposted_count,
        'posted_count': posted_count,
        'completed_steps': completed_steps,
        'total_steps': total_steps,
    })


@login_required
def period_close_action(request, tenant_slug, pk):
    """Close a fiscal period."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    period = get_object_or_404(FiscalPeriod, pk=pk, tenant=tenant)

    if request.method == 'POST':
        # Validate all checklist items are completed
        incomplete = PeriodCloseChecklist.objects.filter(
            tenant=tenant, fiscal_period=period, is_completed=False
        ).count()
        if incomplete > 0:
            messages.error(request, f'{incomplete} checklist items are not yet completed.')
        else:
            # Check for unposted entries
            unposted = JournalEntry.objects.filter(
                tenant=tenant, fiscal_period=period
            ).exclude(status__in=['posted', 'rejected']).count()
            if unposted > 0:
                messages.error(request, f'{unposted} journal entries are not posted. Post or reject them before closing.')
            else:
                period.is_closed = True
                period.save()
                messages.success(request, f'Period "{period}" has been closed.')

    return redirect('general_ledger:period_close_list', tenant_slug=tenant_slug)


@login_required
def period_reopen_action(request, tenant_slug, pk):
    """Reopen a closed fiscal period."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    period = get_object_or_404(FiscalPeriod, pk=pk, tenant=tenant)

    if request.method == 'POST':
        period.is_closed = False
        period.save()
        messages.success(request, f'Period "{period}" has been reopened.')

    return redirect('general_ledger:period_close_list', tenant_slug=tenant_slug)


# =============================================================================
# Account Reconciliation Views
# =============================================================================

@login_required
def reconciliation_list(request, tenant_slug):
    """List all account reconciliations."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = AccountReconciliation.objects.filter(tenant=tenant).select_related(
        'account', 'fiscal_period', 'reconciled_by'
    )

    # Stats
    total_count = qs.count()
    reconciled_count = qs.filter(status='reconciled').count()
    discrepancy_count = qs.filter(status='discrepancy').count()
    pending_count = qs.filter(status='pending').count()

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(account__account_number__icontains=search_query) |
            Q(account__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'general_ledger/reconciliation/reconciliation_list.html', {
        'reconciliations': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'reconciled_count': reconciled_count,
        'discrepancy_count': discrepancy_count,
        'pending_count': pending_count,
    })


@login_required
def reconciliation_create(request, tenant_slug):
    """Create a new reconciliation."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AccountReconciliationForm(request.POST, tenant=tenant)
        if form.is_valid():
            recon = form.save(commit=False)
            recon.tenant = tenant

            # Compute expected balance from posted journal lines
            lines = JournalEntryLine.objects.filter(
                account=recon.account,
                journal_entry__status='posted',
                journal_entry__fiscal_period=recon.fiscal_period,
            )
            totals = lines.aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit')
            )
            debit = totals['total_debit'] or Decimal('0.00')
            credit = totals['total_credit'] or Decimal('0.00')
            if recon.account.account_type.normal_balance == 'debit':
                recon.expected_balance = debit - credit
            else:
                recon.expected_balance = credit - debit

            recon.save()
            messages.success(request, 'Reconciliation created.')
            return redirect('general_ledger:reconciliation_form', tenant_slug=tenant_slug, pk=recon.pk)
    else:
        form = AccountReconciliationForm(tenant=tenant)

    return render(request, 'general_ledger/reconciliation/reconciliation_form.html', {
        'form': form,
        'title': 'New Reconciliation',
    })


@login_required
def reconciliation_form(request, tenant_slug, pk):
    """Edit an existing reconciliation."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    recon = get_object_or_404(AccountReconciliation, pk=pk, tenant=tenant)

    # Get transaction lines for this account in this period
    lines = JournalEntryLine.objects.filter(
        account=recon.account,
        journal_entry__status='posted',
        journal_entry__fiscal_period=recon.fiscal_period,
    ).select_related('journal_entry')

    if request.method == 'POST':
        form = AccountReconciliationForm(request.POST, instance=recon, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.difference == Decimal('0.00'):
                obj.reconciled_by = request.user
                obj.reconciled_at = timezone.now()
            obj.save()
            messages.success(request, 'Reconciliation updated.')
            return redirect('general_ledger:reconciliation_list', tenant_slug=tenant_slug)
    else:
        form = AccountReconciliationForm(instance=recon, tenant=tenant)

    return render(request, 'general_ledger/reconciliation/reconciliation_form.html', {
        'form': form,
        'recon': recon,
        'lines': lines,
        'title': f'Reconcile: {recon.account}',
    })


# =============================================================================
# Allocation Rule Views
# =============================================================================

@login_required
def allocation_list(request, tenant_slug):
    """List all allocation rules."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = AllocationRule.objects.filter(tenant=tenant).select_related('source_account')

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(source_account__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'general_ledger/allocation/allocation_list.html', {
        'allocations': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
    })


@login_required
def allocation_create(request, tenant_slug):
    """Create a new allocation rule."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AllocationRuleForm(request.POST, tenant=tenant)
        formset = AllocationRuleLineFormSet(request.POST, prefix='lines')

        for f in formset.forms:
            f.fields['target_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

        if form.is_valid() and formset.is_valid():
            rule = form.save(commit=False)
            rule.tenant = tenant
            rule.save()
            formset.instance = rule
            formset.save()
            messages.success(request, f'Allocation rule "{rule.name}" created.')
            return redirect('general_ledger:allocation_list', tenant_slug=tenant_slug)
    else:
        form = AllocationRuleForm(tenant=tenant)
        formset = AllocationRuleLineFormSet(prefix='lines')
        for f in formset.forms:
            f.fields['target_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

    return render(request, 'general_ledger/allocation/allocation_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Allocation Rule',
    })


@login_required
def allocation_edit(request, tenant_slug, pk):
    """Edit an allocation rule."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    rule = get_object_or_404(AllocationRule, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AllocationRuleForm(request.POST, instance=rule, tenant=tenant)
        formset = AllocationRuleLineFormSet(request.POST, instance=rule, prefix='lines')

        for f in formset.forms:
            f.fields['target_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Allocation rule "{rule.name}" updated.')
            return redirect('general_ledger:allocation_list', tenant_slug=tenant_slug)
    else:
        form = AllocationRuleForm(instance=rule, tenant=tenant)
        formset = AllocationRuleLineFormSet(instance=rule, prefix='lines')
        for f in formset.forms:
            f.fields['target_account'].queryset = Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )

    return render(request, 'general_ledger/allocation/allocation_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {rule.name}',
        'rule': rule,
    })


@login_required
def allocation_run(request, tenant_slug, pk):
    """Run an allocation rule — generates a journal entry."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    rule = get_object_or_404(AllocationRule, pk=pk, tenant=tenant)

    if request.method == 'POST':
        if not rule.is_active:
            messages.error(request, 'Cannot run an inactive allocation rule.')
            return redirect('general_ledger:allocation_list', tenant_slug=tenant_slug)

        # Get source account balance
        source_balance = rule.source_account.balance
        if source_balance == Decimal('0.00'):
            messages.error(request, 'Source account has zero balance. Nothing to allocate.')
            return redirect('general_ledger:allocation_list', tenant_slug=tenant_slug)

        # Get current fiscal period
        current_period = FiscalPeriod.objects.filter(
            tenant=tenant, is_closed=False
        ).order_by('period_number').first()
        if not current_period:
            messages.error(request, 'No open fiscal period available.')
            return redirect('general_ledger:allocation_list', tenant_slug=tenant_slug)

        # Get default currency
        company_settings = CompanySettings.unscoped.filter(tenant=tenant).first()
        currency = company_settings.base_currency if company_settings else None
        if not currency:
            messages.error(request, 'No base currency configured.')
            return redirect('general_ledger:allocation_list', tenant_slug=tenant_slug)

        # Create journal entry
        je = JournalEntry.objects.create(
            tenant=tenant,
            entry_number=JournalEntry.generate_entry_number(tenant),
            date=timezone.now().date(),
            description=f'Allocation: {rule.name}',
            fiscal_period=current_period,
            status='draft',
            source='allocation',
            currency=currency,
            created_by=request.user,
        )

        # Create lines — credit source, debit targets
        for line in rule.lines.all():
            amount = (source_balance * line.percentage / Decimal('100')).quantize(Decimal('0.01'))
            if amount > 0:
                # Debit target
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=line.target_account,
                    description=f'Allocation from {rule.source_account}',
                    debit=amount,
                    credit=Decimal('0.00'),
                )

        # Credit source for total
        total_allocated = je.lines.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
        if total_allocated > 0:
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=rule.source_account,
                description=f'Allocation to targets',
                debit=Decimal('0.00'),
                credit=total_allocated,
            )

        messages.success(request, f'Allocation generated journal entry "{je.entry_number}".')
        return redirect('general_ledger:journal_detail', tenant_slug=tenant_slug, pk=je.pk)

    return redirect('general_ledger:allocation_list', tenant_slug=tenant_slug)


# =============================================================================
# Audit Trail Views
# =============================================================================

@login_required
def audit_list(request, tenant_slug):
    """View audit trail log."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = AuditTrail.objects.filter(tenant=tenant).select_related('user')

    # Filters
    action_filter = request.GET.get('action', '')
    if action_filter:
        qs = qs.filter(action=action_filter)

    table_filter = request.GET.get('table', '')
    if table_filter:
        qs = qs.filter(table_name__icontains=table_filter)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    # Pagination
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'general_ledger/audit_trail/audit_list.html', {
        'audit_entries': page_obj,
        'page_obj': page_obj,
    })


# =============================================================================
# Exchange Rate Views
# =============================================================================

@login_required
def exchange_rate_list(request, tenant_slug):
    """List exchange rates."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = ExchangeRate.objects.filter(tenant=tenant).select_related(
        'from_currency', 'to_currency'
    )

    # Stats
    total_count = qs.count()

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(from_currency__code__icontains=search_query) |
            Q(to_currency__code__icontains=search_query)
        )

    # Date filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        qs = qs.filter(effective_date__gte=date_from)
    if date_to:
        qs = qs.filter(effective_date__lte=date_to)

    # Pagination
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'general_ledger/currency/exchange_rate_list.html', {
        'exchange_rates': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
    })


@login_required
def exchange_rate_create(request, tenant_slug):
    """Create a new exchange rate."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = ExchangeRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.tenant = tenant
            rate.save()
            messages.success(request, 'Exchange rate created.')
            return redirect('general_ledger:exchange_rate_list', tenant_slug=tenant_slug)
    else:
        form = ExchangeRateForm()

    return render(request, 'general_ledger/currency/exchange_rate_form.html', {
        'form': form,
        'title': 'Add Exchange Rate',
    })


@login_required
def exchange_rate_edit(request, tenant_slug, pk):
    """Edit an exchange rate."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    rate = get_object_or_404(ExchangeRate, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ExchangeRateForm(request.POST, instance=rate)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exchange rate updated.')
            return redirect('general_ledger:exchange_rate_list', tenant_slug=tenant_slug)
    else:
        form = ExchangeRateForm(instance=rate)

    return render(request, 'general_ledger/currency/exchange_rate_form.html', {
        'form': form,
        'title': 'Edit Exchange Rate',
    })

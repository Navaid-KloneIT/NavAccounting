from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant
from apps.general_ledger.models import JournalEntryLine

from .forms import (
    BankAccountForm, BankAccountSignatoryFormSet,
    BankFeedForm, BankTransactionFilterForm, BankTransactionImportForm,
    BankReconciliationForm, AutoMatchRuleForm,
    CashForecastForm, CashForecastLineFormSet,
    IntercompanyTransferForm, BankFeeForm, BankFeeFilterForm,
)
from .models import (
    BankAccount, BankAccountSignatory, BankFeed, BankTransaction,
    BankReconciliation, ReconciliationItem, AutoMatchRule,
    CashForecast, CashForecastLine, IntercompanyTransfer, BankFee,
)
from .services import (
    create_transfer_journal_entry, update_bank_account_balance,
    run_auto_match, compute_cash_position, parse_csv_transactions,
    compute_forecast_variance,
)


# =============================================================================
# 1. Bank Account Management
# =============================================================================

@login_required
def bank_account_list(request, tenant_slug):
    """List bank accounts with search, filters, and stat cards."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = BankAccount.objects.filter(tenant=tenant).select_related('gl_account', 'currency')

    # Stats
    total_count = qs.count()
    active_count = qs.filter(is_active=True).count()
    inactive_count = qs.filter(is_active=False).count()
    total_balance = qs.filter(is_active=True).aggregate(
        total=Sum('current_balance')
    )['total'] or Decimal('0.00')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(account_number_display__icontains=search_query) |
            Q(bank_name__icontains=search_query) |
            Q(account_number__icontains=search_query)
        )

    # Type filter
    type_filter = request.GET.get('type', '')
    if type_filter:
        qs = qs.filter(account_type=type_filter)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'cash_management/bank_accounts/bank_account_list.html', {
        'bank_accounts': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_balance': total_balance,
    })


@login_required
def bank_account_create(request, tenant_slug):
    """Create a new bank account with signatories."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BankAccountForm(request.POST, tenant=tenant)
        formset = BankAccountSignatoryFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            account = form.save(commit=False)
            account.tenant = tenant
            account.account_number_display = BankAccount.generate_account_number(tenant)
            account.current_balance = account.opening_balance
            account.save()

            formset.instance = account
            formset.save()

            messages.success(request, f'Bank account "{account.bank_name}" created.')
            return redirect('cash_management:bank_account_detail',
                            tenant_slug=tenant_slug, pk=account.pk)
    else:
        form = BankAccountForm(tenant=tenant)
        formset = BankAccountSignatoryFormSet()

    return render(request, 'cash_management/bank_accounts/bank_account_form.html', {
        'form': form,
        'signatory_formset': formset,
        'is_edit': False,
    })


@login_required
def bank_account_edit(request, tenant_slug, pk):
    """Edit an existing bank account."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    account = get_object_or_404(BankAccount.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=account, tenant=tenant)
        formset = BankAccountSignatoryFormSet(request.POST, instance=account)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Bank account "{account.bank_name}" updated.')
            return redirect('cash_management:bank_account_detail',
                            tenant_slug=tenant_slug, pk=account.pk)
    else:
        form = BankAccountForm(instance=account, tenant=tenant)
        formset = BankAccountSignatoryFormSet(instance=account)

    return render(request, 'cash_management/bank_accounts/bank_account_form.html', {
        'form': form,
        'signatory_formset': formset,
        'bank_account': account,
        'is_edit': True,
    })


@login_required
def bank_account_detail(request, tenant_slug, pk):
    """Bank account detail with recent transactions and reconciliations."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    account = get_object_or_404(
        BankAccount.unscoped.select_related('gl_account', 'currency'),
        pk=pk, tenant=tenant
    )

    signatories = account.signatories.filter(is_active=True)
    recent_transactions = BankTransaction.unscoped.filter(
        bank_account=account
    ).order_by('-transaction_date')[:10]
    recent_reconciliations = BankReconciliation.unscoped.filter(
        bank_account=account
    ).order_by('-statement_date')[:5]
    feeds = BankFeed.unscoped.filter(bank_account=account)

    return render(request, 'cash_management/bank_accounts/bank_account_detail.html', {
        'bank_account': account,
        'signatories': signatories,
        'recent_transactions': recent_transactions,
        'recent_reconciliations': recent_reconciliations,
        'feeds': feeds,
    })


@login_required
def bank_account_toggle_active(request, tenant_slug, pk):
    """Toggle bank account active status."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        account = get_object_or_404(BankAccount.unscoped, pk=pk, tenant=tenant)
        account.is_active = not account.is_active
        account.save(update_fields=['is_active', 'updated_at'])
        status = 'activated' if account.is_active else 'deactivated'
        messages.success(request, f'Bank account "{account.bank_name}" {status}.')

    return redirect('cash_management:bank_account_list', tenant_slug=tenant_slug)


# =============================================================================
# 2. Bank Feeds
# =============================================================================

@login_required
def bank_feed_list(request, tenant_slug):
    """List bank feed connections."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    feeds = BankFeed.objects.filter(tenant=tenant).select_related('bank_account')

    return render(request, 'cash_management/bank_feeds/bank_feed_list.html', {
        'feeds': feeds,
    })


@login_required
def bank_feed_create(request, tenant_slug):
    """Create a new bank feed connection."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BankFeedForm(request.POST, tenant=tenant)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.tenant = tenant
            feed.save()
            messages.success(request, 'Bank feed connection created.')
            return redirect('cash_management:bank_feed_list', tenant_slug=tenant_slug)
    else:
        form = BankFeedForm(tenant=tenant)

    return render(request, 'cash_management/bank_feeds/bank_feed_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def bank_feed_edit(request, tenant_slug, pk):
    """Edit a bank feed connection."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    feed = get_object_or_404(BankFeed.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BankFeedForm(request.POST, instance=feed, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank feed updated.')
            return redirect('cash_management:bank_feed_list', tenant_slug=tenant_slug)
    else:
        form = BankFeedForm(instance=feed, tenant=tenant)

    return render(request, 'cash_management/bank_feeds/bank_feed_form.html', {
        'form': form,
        'feed': feed,
        'is_edit': True,
    })


# =============================================================================
# 3. Bank Transactions
# =============================================================================

@login_required
def bank_transaction_list(request, tenant_slug):
    """List bank transactions with filters."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = BankTransaction.objects.filter(tenant=tenant).select_related('bank_account')

    # Stats
    total_count = qs.count()
    matched_count = qs.filter(is_matched=True).count()
    unmatched_count = qs.filter(is_matched=False).count()
    total_amount = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Filters
    filter_form = BankTransactionFilterForm(request.GET, tenant=tenant)

    bank_account_id = request.GET.get('bank_account', '')
    if bank_account_id:
        qs = qs.filter(bank_account_id=bank_account_id)

    date_from = request.GET.get('date_from', '')
    if date_from:
        qs = qs.filter(transaction_date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        qs = qs.filter(transaction_date__lte=date_to)

    txn_type = request.GET.get('transaction_type', '')
    if txn_type:
        qs = qs.filter(transaction_type=txn_type)

    matched = request.GET.get('matched', '')
    if matched == 'yes':
        qs = qs.filter(is_matched=True)
    elif matched == 'no':
        qs = qs.filter(is_matched=False)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(transaction_number__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(reference__icontains=search_query)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'cash_management/transactions/bank_transaction_list.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': total_count,
        'matched_count': matched_count,
        'unmatched_count': unmatched_count,
        'total_amount': total_amount,
    })


@login_required
def bank_transaction_import(request, tenant_slug):
    """Import bank transactions from CSV file."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    created_count = 0
    errors = []

    if request.method == 'POST':
        form = BankTransactionImportForm(request.POST, request.FILES, tenant=tenant)
        if form.is_valid():
            bank_account = form.cleaned_data['bank_account']
            file = form.cleaned_data['file']
            created_count, errors = parse_csv_transactions(file, bank_account, tenant)
            if created_count > 0:
                messages.success(request, f'{created_count} transactions imported successfully.')
            if errors:
                for error in errors[:5]:
                    messages.warning(request, error)
                if len(errors) > 5:
                    messages.warning(request, f'... and {len(errors) - 5} more errors.')
            if created_count > 0:
                return redirect('cash_management:bank_transaction_list', tenant_slug=tenant_slug)
    else:
        form = BankTransactionImportForm(tenant=tenant)

    return render(request, 'cash_management/transactions/bank_transaction_import.html', {
        'form': form,
        'created_count': created_count,
        'errors': errors,
    })


@login_required
def bank_transaction_detail(request, tenant_slug, pk):
    """View bank transaction details."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    transaction = get_object_or_404(
        BankTransaction.unscoped.select_related('bank_account', 'matched_journal_entry'),
        pk=pk, tenant=tenant
    )

    return render(request, 'cash_management/transactions/bank_transaction_detail.html', {
        'transaction': transaction,
    })


# =============================================================================
# 4. Reconciliation Engine
# =============================================================================

@login_required
def reconciliation_list(request, tenant_slug):
    """List bank reconciliations."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = BankReconciliation.objects.filter(tenant=tenant).select_related(
        'bank_account', 'fiscal_period', 'reconciled_by'
    )

    # Stats
    total_count = qs.count()
    completed_count = qs.filter(status='completed').count()
    in_progress_count = qs.filter(status='in_progress').count()
    reviewed_count = qs.filter(status='reviewed').count()

    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    bank_account_id = request.GET.get('bank_account', '')
    if bank_account_id:
        qs = qs.filter(bank_account_id=bank_account_id)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    bank_accounts = BankAccount.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'cash_management/reconciliation/reconciliation_list.html', {
        'reconciliations': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'reviewed_count': reviewed_count,
        'bank_accounts': bank_accounts,
    })


@login_required
def reconciliation_start(request, tenant_slug):
    """Start a new bank reconciliation."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BankReconciliationForm(request.POST, tenant=tenant)
        if form.is_valid():
            recon = form.save(commit=False)
            recon.tenant = tenant

            # Compute GL balance from posted journal lines
            gl_account = recon.bank_account.gl_account
            lines = JournalEntryLine.objects.filter(
                account=gl_account,
                journal_entry__status='posted',
                journal_entry__date__lte=recon.statement_date,
            )
            totals = lines.aggregate(
                total_debit=Sum('debit'), total_credit=Sum('credit')
            )
            debit = totals['total_debit'] or Decimal('0.00')
            credit = totals['total_credit'] or Decimal('0.00')
            recon.gl_balance = debit - credit  # Asset accounts have debit normal balance
            recon.adjusted_balance = recon.gl_balance
            recon.save()

            messages.success(request, 'Reconciliation started.')
            return redirect('cash_management:reconciliation_workspace',
                            tenant_slug=tenant_slug, pk=recon.pk)
    else:
        form = BankReconciliationForm(tenant=tenant)

    return render(request, 'cash_management/reconciliation/reconciliation_start.html', {
        'form': form,
    })


@login_required
def reconciliation_workspace(request, tenant_slug, pk):
    """Reconciliation workspace - two-panel matching UI."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    recon = get_object_or_404(
        BankReconciliation.unscoped.select_related('bank_account', 'fiscal_period'),
        pk=pk, tenant=tenant
    )

    # Unmatched bank transactions
    unmatched_txns = BankTransaction.unscoped.filter(
        bank_account=recon.bank_account,
        is_matched=False,
        transaction_date__gte=recon.fiscal_period.start_date,
        transaction_date__lte=recon.fiscal_period.end_date,
    ).order_by('transaction_date')

    # Unmatched GL entries
    gl_account = recon.bank_account.gl_account
    matched_line_ids = ReconciliationItem.objects.filter(
        reconciliation=recon, status='matched', journal_entry_line__isnull=False
    ).values_list('journal_entry_line_id', flat=True)

    unmatched_gl = JournalEntryLine.objects.filter(
        account=gl_account,
        journal_entry__status='posted',
        journal_entry__date__gte=recon.fiscal_period.start_date,
        journal_entry__date__lte=recon.fiscal_period.end_date,
    ).exclude(id__in=matched_line_ids).select_related('journal_entry')

    # Matched items
    matched_items = ReconciliationItem.objects.filter(
        reconciliation=recon, status='matched'
    ).select_related('bank_transaction', 'journal_entry_line')

    # Summary
    matched_count = matched_items.count()
    unmatched_txn_count = unmatched_txns.count()
    unmatched_gl_count = unmatched_gl.count()

    return render(request, 'cash_management/reconciliation/reconciliation_workspace.html', {
        'recon': recon,
        'unmatched_txns': unmatched_txns,
        'unmatched_gl': unmatched_gl,
        'matched_items': matched_items,
        'matched_count': matched_count,
        'unmatched_txn_count': unmatched_txn_count,
        'unmatched_gl_count': unmatched_gl_count,
    })


@login_required
def reconciliation_match(request, tenant_slug, pk):
    """Match a bank transaction to a GL entry line."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        recon = get_object_or_404(BankReconciliation.unscoped, pk=pk, tenant=tenant)
        txn_id = request.POST.get('transaction_id')
        gl_line_id = request.POST.get('gl_line_id')

        txn = get_object_or_404(BankTransaction.unscoped, pk=txn_id)
        gl_line = get_object_or_404(JournalEntryLine, pk=gl_line_id)

        ReconciliationItem.objects.create(
            reconciliation=recon,
            bank_transaction=txn,
            journal_entry_line=gl_line,
            match_type='manual',
            status='matched',
            amount=txn.amount,
        )
        txn.is_matched = True
        txn.save(update_fields=['is_matched', 'updated_at'])

        # Update adjusted balance
        matched_total = ReconciliationItem.objects.filter(
            reconciliation=recon, status='matched'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        recon.adjusted_balance = recon.gl_balance + matched_total
        recon.save(update_fields=['adjusted_balance', 'updated_at'])

        messages.success(request, 'Items matched successfully.')

    return redirect('cash_management:reconciliation_workspace',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def reconciliation_unmatch(request, tenant_slug, pk):
    """Unmatch a reconciliation item."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        recon = get_object_or_404(BankReconciliation.unscoped, pk=pk, tenant=tenant)
        item_id = request.POST.get('item_id')
        item = get_object_or_404(ReconciliationItem, pk=item_id, reconciliation=recon)

        if item.bank_transaction:
            item.bank_transaction.is_matched = False
            item.bank_transaction.save(update_fields=['is_matched', 'updated_at'])

        item.delete()
        messages.success(request, 'Match removed.')

    return redirect('cash_management:reconciliation_workspace',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def reconciliation_auto_match(request, tenant_slug, pk):
    """Run auto-match rules on a reconciliation."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        recon = get_object_or_404(BankReconciliation.unscoped, pk=pk, tenant=tenant)
        match_count = run_auto_match(recon)
        messages.success(request, f'{match_count} items auto-matched.')

    return redirect('cash_management:reconciliation_workspace',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def reconciliation_complete(request, tenant_slug, pk):
    """Complete a reconciliation."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        recon = get_object_or_404(BankReconciliation.unscoped, pk=pk, tenant=tenant)
        recon.status = 'completed'
        recon.reconciled_by = request.user
        recon.reconciled_at = timezone.now()
        recon.save()

        update_bank_account_balance(recon.bank_account)
        messages.success(request, 'Reconciliation completed.')

    return redirect('cash_management:reconciliation_workspace',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def auto_match_rule_list(request, tenant_slug):
    """List auto-match rules."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    rules = AutoMatchRule.objects.filter(tenant=tenant).order_by('priority')

    return render(request, 'cash_management/reconciliation/auto_match_rule_list.html', {
        'rules': rules,
    })


@login_required
def auto_match_rule_create(request, tenant_slug):
    """Create a new auto-match rule."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = AutoMatchRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.tenant = tenant
            rule.save()
            messages.success(request, f'Match rule "{rule.name}" created.')
            return redirect('cash_management:auto_match_rule_list', tenant_slug=tenant_slug)
    else:
        form = AutoMatchRuleForm()

    return render(request, 'cash_management/reconciliation/auto_match_rule_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def auto_match_rule_edit(request, tenant_slug, pk):
    """Edit an auto-match rule."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    rule = get_object_or_404(AutoMatchRule.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = AutoMatchRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Match rule "{rule.name}" updated.')
            return redirect('cash_management:auto_match_rule_list', tenant_slug=tenant_slug)
    else:
        form = AutoMatchRuleForm(instance=rule)

    return render(request, 'cash_management/reconciliation/auto_match_rule_form.html', {
        'form': form,
        'rule': rule,
        'is_edit': True,
    })


# =============================================================================
# 5. Cash Positioning
# =============================================================================

@login_required
def cash_position_dashboard(request, tenant_slug):
    """Real-time cash position dashboard."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    as_of_date = request.GET.get('date')
    if as_of_date:
        from datetime import datetime
        try:
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        except ValueError:
            as_of_date = None

    position = compute_cash_position(tenant, as_of_date)

    return render(request, 'cash_management/cash_position/cash_position_dashboard.html', {
        'position': position,
    })


# =============================================================================
# 6. Treasury Forecasting
# =============================================================================

@login_required
def forecast_list(request, tenant_slug):
    """List cash forecasts."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = CashForecast.objects.filter(tenant=tenant).select_related('created_by')

    # Stats
    total_count = qs.count()
    active_count = qs.filter(status='active').count()
    draft_count = qs.filter(status='draft').count()

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'cash_management/forecasts/forecast_list.html', {
        'forecasts': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'draft_count': draft_count,
    })


@login_required
def forecast_create(request, tenant_slug):
    """Create a new cash forecast with line items."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = CashForecastForm(request.POST)
        formset = CashForecastLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            forecast = form.save(commit=False)
            forecast.tenant = tenant
            forecast.forecast_number = CashForecast.generate_forecast_number(tenant)
            forecast.created_by = request.user
            forecast.save()

            formset.instance = forecast
            formset.save()

            messages.success(request, f'Forecast "{forecast.name}" created.')
            return redirect('cash_management:forecast_detail',
                            tenant_slug=tenant_slug, pk=forecast.pk)
    else:
        form = CashForecastForm()
        formset = CashForecastLineFormSet()

    return render(request, 'cash_management/forecasts/forecast_form.html', {
        'form': form,
        'line_formset': formset,
        'is_edit': False,
    })


@login_required
def forecast_detail(request, tenant_slug, pk):
    """View forecast detail with chart and lines."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    forecast = get_object_or_404(
        CashForecast.unscoped.select_related('created_by'),
        pk=pk, tenant=tenant
    )
    lines = forecast.lines.all()

    # Compute totals
    total_expected = lines.aggregate(total=Sum('expected_amount'))['total'] or Decimal('0.00')
    total_actual = lines.filter(actual_amount__isnull=False).aggregate(
        total=Sum('actual_amount')
    )['total'] or Decimal('0.00')

    # Chart data
    chart_labels = [line.line_date.strftime('%Y-%m-%d') for line in lines]
    chart_expected = [float(line.expected_amount) for line in lines]
    chart_actual = [float(line.actual_amount) if line.actual_amount else None for line in lines]

    return render(request, 'cash_management/forecasts/forecast_detail.html', {
        'forecast': forecast,
        'lines': lines,
        'total_expected': total_expected,
        'total_actual': total_actual,
        'chart_labels': chart_labels,
        'chart_expected': chart_expected,
        'chart_actual': chart_actual,
    })


@login_required
def forecast_edit(request, tenant_slug, pk):
    """Edit a cash forecast."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    forecast = get_object_or_404(CashForecast.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = CashForecastForm(request.POST, instance=forecast)
        formset = CashForecastLineFormSet(request.POST, instance=forecast)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            compute_forecast_variance(forecast)
            messages.success(request, f'Forecast "{forecast.name}" updated.')
            return redirect('cash_management:forecast_detail',
                            tenant_slug=tenant_slug, pk=forecast.pk)
    else:
        form = CashForecastForm(instance=forecast)
        formset = CashForecastLineFormSet(instance=forecast)

    return render(request, 'cash_management/forecasts/forecast_form.html', {
        'form': form,
        'line_formset': formset,
        'forecast': forecast,
        'is_edit': True,
    })


# =============================================================================
# 7. Inter-company Transfers
# =============================================================================

@login_required
def transfer_list(request, tenant_slug):
    """List inter-company transfers."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = IntercompanyTransfer.objects.filter(tenant=tenant).select_related(
        'from_bank_account', 'to_bank_account', 'currency', 'created_by'
    )

    # Stats
    total_count = qs.count()
    pending_count = qs.filter(status='pending').count()
    completed_count = qs.filter(status='completed').count()
    total_amount = qs.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'cash_management/transfers/transfer_list.html', {
        'transfers': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'total_amount': total_amount,
    })


@login_required
def transfer_create(request, tenant_slug):
    """Create a new inter-company transfer."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = IntercompanyTransferForm(request.POST, tenant=tenant)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.tenant = tenant
            transfer.transfer_number = IntercompanyTransfer.generate_transfer_number(tenant)
            transfer.created_by = request.user
            transfer.save()

            messages.success(request, f'Transfer {transfer.transfer_number} created.')
            return redirect('cash_management:transfer_detail',
                            tenant_slug=tenant_slug, pk=transfer.pk)
    else:
        form = IntercompanyTransferForm(tenant=tenant)

    return render(request, 'cash_management/transfers/transfer_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def transfer_detail(request, tenant_slug, pk):
    """View transfer details."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    transfer = get_object_or_404(
        IntercompanyTransfer.unscoped.select_related(
            'from_bank_account', 'to_bank_account', 'currency',
            'created_by', 'approved_by', 'journal_entry'
        ),
        pk=pk, tenant=tenant
    )

    return render(request, 'cash_management/transfers/transfer_detail.html', {
        'transfer': transfer,
    })


@login_required
def transfer_approve(request, tenant_slug, pk):
    """Approve a transfer."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        transfer = get_object_or_404(
            IntercompanyTransfer.unscoped, pk=pk, tenant=tenant, status='draft'
        )
        transfer.status = 'pending'
        transfer.approved_by = request.user
        transfer.save(update_fields=['status', 'approved_by', 'updated_at'])
        messages.success(request, f'Transfer {transfer.transfer_number} approved.')

    return redirect('cash_management:transfer_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def transfer_complete(request, tenant_slug, pk):
    """Complete a transfer and create GL journal entry."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        transfer = get_object_or_404(
            IntercompanyTransfer.unscoped, pk=pk, tenant=tenant, status='pending'
        )

        # Create journal entry
        je = create_transfer_journal_entry(transfer, tenant, request.user)

        transfer.status = 'completed'
        transfer.journal_entry = je
        transfer.save(update_fields=['status', 'journal_entry', 'updated_at'])

        # Update bank account balances
        update_bank_account_balance(transfer.from_bank_account)
        update_bank_account_balance(transfer.to_bank_account)

        messages.success(request, f'Transfer {transfer.transfer_number} completed. Journal entry {je.entry_number} created.')

    return redirect('cash_management:transfer_detail',
                    tenant_slug=tenant_slug, pk=pk)


@login_required
def transfer_cancel(request, tenant_slug, pk):
    """Cancel a transfer."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    if request.method == 'POST':
        transfer = get_object_or_404(
            IntercompanyTransfer.unscoped, pk=pk, tenant=tenant
        )
        if transfer.status in ('draft', 'pending'):
            transfer.status = 'cancelled'
            transfer.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Transfer {transfer.transfer_number} cancelled.')
        else:
            messages.error(request, 'Cannot cancel a completed transfer.')

    return redirect('cash_management:transfer_detail',
                    tenant_slug=tenant_slug, pk=pk)


# =============================================================================
# 8. Bank Fee Analysis
# =============================================================================

@login_required
def bank_fee_list(request, tenant_slug):
    """List bank fees with filters."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    qs = BankFee.objects.filter(tenant=tenant).select_related('bank_account')

    # Stats
    total_count = qs.count()
    total_fees = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    recurring_count = qs.filter(is_recurring=True).count()

    # Filters
    filter_form = BankFeeFilterForm(request.GET, tenant=tenant)

    bank_account_id = request.GET.get('bank_account', '')
    if bank_account_id:
        qs = qs.filter(bank_account_id=bank_account_id)

    date_from = request.GET.get('date_from', '')
    if date_from:
        qs = qs.filter(fee_date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        qs = qs.filter(fee_date__lte=date_to)

    fee_type = request.GET.get('fee_type', '')
    if fee_type:
        qs = qs.filter(fee_type=fee_type)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'cash_management/bank_fees/bank_fee_list.html', {
        'fees': page_obj,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': total_count,
        'total_fees': total_fees,
        'recurring_count': recurring_count,
    })


@login_required
def bank_fee_create(request, tenant_slug):
    """Create a new bank fee record."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    if request.method == 'POST':
        form = BankFeeForm(request.POST, tenant=tenant)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.tenant = tenant
            fee.save()
            messages.success(request, 'Bank fee recorded.')
            return redirect('cash_management:bank_fee_list', tenant_slug=tenant_slug)
    else:
        form = BankFeeForm(tenant=tenant)

    return render(request, 'cash_management/bank_fees/bank_fee_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def bank_fee_edit(request, tenant_slug, pk):
    """Edit a bank fee record."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    fee = get_object_or_404(BankFee.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = BankFeeForm(request.POST, instance=fee, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank fee updated.')
            return redirect('cash_management:bank_fee_list', tenant_slug=tenant_slug)
    else:
        form = BankFeeForm(instance=fee, tenant=tenant)

    return render(request, 'cash_management/bank_fees/bank_fee_form.html', {
        'form': form,
        'fee': fee,
        'is_edit': True,
    })


@login_required
def bank_fee_analysis(request, tenant_slug):
    """Bank fee analysis dashboard with charts."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)
    fees = BankFee.objects.filter(tenant=tenant).select_related('bank_account')

    # Total fees
    total_fees = fees.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Fee breakdown by type
    fee_by_type = fees.values('fee_type').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Fee by bank account
    fee_by_account = fees.values(
        'bank_account__account_number_display', 'bank_account__bank_name'
    ).annotate(total=Sum('amount')).order_by('-total')

    # Monthly trend (last 12 months)
    from django.db.models.functions import TruncMonth
    monthly_trend = fees.annotate(
        month=TruncMonth('fee_date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')[:12]

    # Chart data
    type_labels = [dict(BankFee.FEE_TYPE_CHOICES).get(item['fee_type'], item['fee_type']) for item in fee_by_type]
    type_values = [float(item['total']) for item in fee_by_type]

    account_labels = [f"{item['bank_account__account_number_display']}" for item in fee_by_account]
    account_values = [float(item['total']) for item in fee_by_account]

    trend_labels = [item['month'].strftime('%b %Y') for item in monthly_trend]
    trend_values = [float(item['total']) for item in monthly_trend]

    return render(request, 'cash_management/bank_fees/bank_fee_analysis.html', {
        'total_fees': total_fees,
        'fee_by_type': fee_by_type,
        'fee_by_account': fee_by_account,
        'type_labels': type_labels,
        'type_values': type_values,
        'account_labels': account_labels,
        'account_values': account_values,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
    })

"""Dashboard KPI calculation and data services — real queries across all modules."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Q, F, Value
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone


def get_kpi_data(tenant):
    """Calculate 4 headline KPI metrics from real module data."""
    from apps.accounts_receivable.models import Invoice
    from apps.accounts_payable.models import Bill
    from apps.cash_management.models import BankAccount
    from apps.inventory.models import Item

    today = date.today()
    zero = Decimal('0.00')

    # Total Revenue — sum of amount_paid on paid/partially_paid invoices
    revenue = Invoice.unscoped.filter(
        tenant=tenant, status__in=['paid', 'partially_paid']
    ).aggregate(total=Coalesce(Sum('amount_paid'), zero))['total']

    # Outstanding Payables — unpaid balance on approved/partially_paid bills
    payables_qs = Bill.unscoped.filter(
        tenant=tenant, status__in=['approved', 'partially_paid', 'pending_approval']
    )
    payables = payables_qs.aggregate(
        total=Coalesce(Sum(F('total_amount') - F('amount_paid')), zero)
    )['total']
    overdue_bills = payables_qs.filter(due_date__lt=today).count()

    # Outstanding Invoices count
    outstanding_invoices = Invoice.unscoped.filter(
        tenant=tenant, status__in=['sent', 'approved', 'partially_paid']
    ).count()

    # Cash Balance — sum of active bank account balances
    bank_agg = BankAccount.unscoped.filter(
        tenant=tenant, is_active=True
    ).aggregate(
        total=Coalesce(Sum('current_balance'), zero),
        count=Sum(Value(1))
    )
    cash_balance = bank_agg['total']
    bank_count = bank_agg['count'] or 0

    # Inventory Value — DB aggregates for weighted_avg and standard items
    inv_wa = Item.unscoped.filter(
        tenant=tenant, is_active=True, item_type='inventory',
        costing_method='weighted_avg'
    ).aggregate(
        total=Coalesce(Sum(F('quantity_on_hand') * F('weighted_avg_cost')), zero)
    )['total']

    inv_std = Item.unscoped.filter(
        tenant=tenant, is_active=True, item_type='inventory',
        costing_method='standard'
    ).aggregate(
        total=Coalesce(Sum(F('quantity_on_hand') * F('standard_cost')), zero)
    )['total']

    # FIFO/LIFO items — must use cost layers
    fifo_lifo_items = Item.unscoped.filter(
        tenant=tenant, is_active=True, item_type='inventory',
        costing_method__in=['fifo', 'lifo']
    ).prefetch_related('cost_layers')
    inv_fifo_lifo = zero
    for item in fifo_lifo_items:
        inv_fifo_lifo += sum(
            (cl.quantity_on_hand * cl.unit_cost for cl in item.cost_layers.filter(is_depleted=False)),
            zero,
        )

    inventory_value = inv_wa + inv_std + inv_fifo_lifo

    return {
        'total_revenue': revenue,
        'total_payables': payables,
        'overdue_bills_count': overdue_bills,
        'outstanding_invoices_count': outstanding_invoices,
        'cash_balance': cash_balance,
        'bank_account_count': bank_count,
        'inventory_value': inventory_value,
    }


def get_cash_flow_data(tenant, months=6):
    """Get real monthly bank inflow/outflow from BankTransactions."""
    from apps.cash_management.models import BankTransaction

    today = date.today()
    start_date = (today.replace(day=1) - timedelta(days=(months - 1) * 28)).replace(day=1)

    txns = (
        BankTransaction.unscoped
        .filter(tenant=tenant, transaction_date__gte=start_date)
        .annotate(month=TruncMonth('transaction_date'))
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # Build month buckets
    categories = []
    inflow_map = {}
    outflow_map = {}
    current = start_date
    while current <= today:
        key = current.strftime('%Y-%m')
        label = current.strftime('%b %Y')
        categories.append(label)
        inflow_map[key] = 0
        outflow_map[key] = 0
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    for row in txns:
        key = row['month'].strftime('%Y-%m')
        if key in inflow_map:
            if row['transaction_type'] == 'credit':
                inflow_map[key] = float(row['total'])
            else:
                outflow_map[key] = float(row['total'])

    inflow = [inflow_map.get(k, 0) for k in inflow_map]
    outflow = [outflow_map.get(k, 0) for k in outflow_map]
    net = [inflow[i] - outflow[i] for i in range(len(inflow))]

    return {
        'categories': categories,
        'inflow': inflow,
        'outflow': outflow,
        'net': net,
    }


def get_module_activity(tenant):
    """Get key activity counts for each module."""
    from apps.general_ledger.models import JournalEntry
    from apps.accounts_payable.models import Bill
    from apps.accounts_receivable.models import Invoice
    from apps.cash_management.models import BankTransaction
    from apps.fixed_assets.models import Asset
    from apps.inventory.models import ReorderSuggestion

    today = date.today()
    month_start = today.replace(day=1)

    return {
        'gl_posted': JournalEntry.unscoped.filter(
            tenant=tenant, status='posted', date__gte=month_start
        ).count(),
        'ap_overdue': Bill.unscoped.filter(
            tenant=tenant, due_date__lt=today,
            status__in=['approved', 'partially_paid', 'pending_approval']
        ).count(),
        'ar_outstanding': Invoice.unscoped.filter(
            tenant=tenant, status__in=['sent', 'partially_paid', 'approved']
        ).count(),
        'cm_unreconciled': BankTransaction.unscoped.filter(
            tenant=tenant, is_matched=False
        ).count(),
        'fa_in_service': Asset.unscoped.filter(
            tenant=tenant, status='in_service'
        ).count(),
        'ic_low_stock': ReorderSuggestion.unscoped.filter(
            tenant=tenant, status='pending'
        ).count(),
    }


def get_revenue_expense_data(tenant, months=6):
    """Get monthly revenue vs expense from posted journal entry lines."""
    from apps.general_ledger.models import JournalEntryLine

    today = date.today()
    start_date = (today.replace(day=1) - timedelta(days=(months - 1) * 28)).replace(day=1)

    # Revenue lines (credit normal balance: revenue = credit - debit)
    revenue_qs = (
        JournalEntryLine.objects
        .filter(
            journal_entry__tenant=tenant,
            journal_entry__status='posted',
            journal_entry__date__gte=start_date,
            account__account_type__code='REVENUE',
        )
        .annotate(month=TruncMonth('journal_entry__date'))
        .values('month')
        .annotate(total=Sum(F('credit') - F('debit')))
        .order_by('month')
    )

    # Expense lines (debit normal balance: expense = debit - credit)
    expense_qs = (
        JournalEntryLine.objects
        .filter(
            journal_entry__tenant=tenant,
            journal_entry__status='posted',
            journal_entry__date__gte=start_date,
            account__account_type__code='EXPENSE',
        )
        .annotate(month=TruncMonth('journal_entry__date'))
        .values('month')
        .annotate(total=Sum(F('debit') - F('credit')))
        .order_by('month')
    )

    # Build month buckets
    categories = []
    rev_map = {}
    exp_map = {}
    current = start_date
    while current <= today:
        key = current.strftime('%Y-%m')
        label = current.strftime('%b')
        categories.append(label)
        rev_map[key] = 0
        exp_map[key] = 0
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    for row in revenue_qs:
        key = row['month'].strftime('%Y-%m')
        if key in rev_map:
            rev_map[key] = float(row['total'] or 0)

    for row in expense_qs:
        key = row['month'].strftime('%Y-%m')
        if key in exp_map:
            exp_map[key] = float(row['total'] or 0)

    return {
        'categories': categories,
        'revenue': list(rev_map.values()),
        'expenses': list(exp_map.values()),
    }


def get_aging_data(tenant):
    """Get AR and AP aging buckets."""
    from apps.accounts_receivable.models import Invoice
    from apps.accounts_payable.models import Bill

    today = date.today()
    labels = ['Current', '1-30', '31-60', '61-90', '90+']
    buckets = [
        Q(due_date__gte=today),                                              # Current
        Q(due_date__lt=today, due_date__gte=today - timedelta(days=30)),     # 1-30
        Q(due_date__lt=today - timedelta(days=30), due_date__gte=today - timedelta(days=60)),  # 31-60
        Q(due_date__lt=today - timedelta(days=60), due_date__gte=today - timedelta(days=90)),  # 61-90
        Q(due_date__lt=today - timedelta(days=90)),                          # 90+
    ]

    zero = Decimal('0.00')
    receivables = []
    payables = []

    ar_base = Invoice.unscoped.filter(
        tenant=tenant, status__in=['sent', 'approved', 'partially_paid']
    )
    ap_base = Bill.unscoped.filter(
        tenant=tenant, status__in=['approved', 'partially_paid', 'pending_approval']
    )

    for q in buckets:
        ar_val = ar_base.filter(q).aggregate(
            total=Coalesce(Sum(F('total_amount') - F('amount_paid')), zero)
        )['total']
        receivables.append(float(ar_val))

        ap_val = ap_base.filter(q).aggregate(
            total=Coalesce(Sum(F('total_amount') - F('amount_paid')), zero)
        )['total']
        payables.append(float(ap_val))

    return {
        'labels': labels,
        'receivables': receivables,
        'payables': payables,
    }


def get_recent_activity(tenant, limit=10):
    """Get last N posted journal entries."""
    from apps.general_ledger.models import JournalEntry

    return list(
        JournalEntry.unscoped
        .filter(tenant=tenant, status='posted')
        .select_related('created_by')
        .order_by('-posted_at', '-date')[:limit]
    )


def get_quick_actions():
    """Return static quick action definitions for all modules."""
    return [
        {'label': 'Create Invoice', 'url_name': 'accounts_receivable:invoice_create', 'icon': 'ri-file-list-3-line', 'color': 'primary'},
        {'label': 'Record Bill', 'url_name': 'accounts_payable:bill_create', 'icon': 'ri-bill-line', 'color': 'danger'},
        {'label': 'Journal Entry', 'url_name': 'general_ledger:journal_create', 'icon': 'ri-book-2-line', 'color': 'info'},
        {'label': 'Record Payment', 'url_name': 'accounts_payable:payment_create', 'icon': 'ri-money-dollar-box-line', 'color': 'success'},
        {'label': 'Bank Reconciliation', 'url_name': 'cash_management:reconciliation_list', 'icon': 'ri-bank-line', 'color': 'warning'},
        {'label': 'Record Receipt', 'url_name': 'accounts_receivable:receipt_create', 'icon': 'ri-hand-coin-line', 'color': 'success'},
        {'label': 'Purchase Order', 'url_name': 'inventory:po_create', 'icon': 'ri-shopping-cart-line', 'color': 'info'},
        {'label': 'Asset Register', 'url_name': 'fixed_assets:asset_list', 'icon': 'ri-building-line', 'color': 'secondary'},
    ]

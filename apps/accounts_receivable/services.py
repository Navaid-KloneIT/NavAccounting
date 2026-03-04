"""Business logic for AR module — receipt journal entries, aging, cash application, etc."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.utils import timezone

from apps.general_ledger.models import JournalEntry, JournalEntryLine


def create_receipt_journal_entry(receipt, tenant, user):
    """
    Create GL journal entry for a completed receipt (payment from customer).
    Debit: Bank/Cash account (increase asset)
    Credit: AR control account (decrease receivable)
    If discount given: Debit Sales Discount expense.
    """
    entry_number = JournalEntry.generate_entry_number(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=entry_number,
        date=receipt.receipt_date,
        description=f"AR Receipt {receipt.receipt_number} from {receipt.customer.display_name}",
        reference=receipt.reference or receipt.check_number or receipt.receipt_number,
        fiscal_period=receipt.fiscal_period,
        status='posted',
        source='ar_receipt',
        currency=receipt.currency,
        exchange_rate=receipt.exchange_rate,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit Bank account (increase asset)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=receipt.bank_account,
        description=f"Receipt from {receipt.customer.display_name}",
        debit=receipt.amount,
        credit=Decimal('0.00'),
    )

    # Credit AR account (decrease receivable)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=receipt.ar_account,
        description=f"Receipt {receipt.receipt_number}",
        debit=Decimal('0.00'),
        credit=receipt.amount + receipt.discount_given,
    )

    # If discount given, debit sales discount expense
    if receipt.discount_given > Decimal('0.00'):
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=receipt.bank_account,
            description=f"Sales discount on {receipt.receipt_number}",
            debit=receipt.discount_given,
            credit=Decimal('0.00'),
        )

    return je


def create_void_receipt_journal_entry(receipt, tenant, user):
    """
    Create reversing GL journal entry for a voided receipt.
    Reverses the original: Debit AR, Credit Bank.
    """
    entry_number = JournalEntry.generate_entry_number(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=entry_number,
        date=timezone.now().date(),
        description=f"VOID: AR Receipt {receipt.receipt_number} from {receipt.customer.display_name}",
        reference=f"VOID-{receipt.receipt_number}",
        fiscal_period=receipt.fiscal_period,
        status='posted',
        source='ar_receipt',
        currency=receipt.currency,
        exchange_rate=receipt.exchange_rate,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit AR account (restore receivable)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=receipt.ar_account,
        description=f"Void receipt from {receipt.customer.display_name}",
        debit=receipt.amount + receipt.discount_given,
        credit=Decimal('0.00'),
    )

    # Credit Bank account (reverse deposit)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=receipt.bank_account,
        description=f"Void receipt {receipt.receipt_number}",
        debit=Decimal('0.00'),
        credit=receipt.amount,
    )

    # Reverse discount if applicable
    if receipt.discount_given > Decimal('0.00'):
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=receipt.bank_account,
            description=f"Reverse discount on {receipt.receipt_number}",
            debit=Decimal('0.00'),
            credit=receipt.discount_given,
        )

    return je


def create_credit_memo_journal_entry(credit_memo, tenant, user):
    """
    GL entry for approved credit memo.
    Debit: AR control account (reduce receivable via contra)
    Credit: AR control account or Revenue account
    """
    entry_number = JournalEntry.generate_entry_number(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=entry_number,
        date=credit_memo.memo_date,
        description=f"Credit Memo {credit_memo.memo_number} for {credit_memo.customer.display_name}",
        reference=credit_memo.memo_number,
        fiscal_period=credit_memo.fiscal_period,
        status='posted',
        source='ar_credit_memo',
        currency_id=None,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit revenue/returns account (reduce revenue)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=credit_memo.ar_account,
        description=f"Credit memo {credit_memo.memo_number}",
        debit=credit_memo.amount,
        credit=Decimal('0.00'),
    )

    # Credit AR account (reduce receivable)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=credit_memo.ar_account,
        description=f"Credit memo for {credit_memo.customer.display_name}",
        debit=Decimal('0.00'),
        credit=credit_memo.amount,
    )

    return je


def create_write_off_journal_entry(write_off, tenant, user):
    """
    GL entry for bad debt write-off.
    Debit: Bad debt expense account
    Credit: AR control account
    """
    entry_number = JournalEntry.generate_entry_number(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=entry_number,
        date=write_off.write_off_date,
        description=f"Write-off: Invoice {write_off.invoice.invoice_number}",
        reference=f"WO-{write_off.invoice.invoice_number}",
        fiscal_period=write_off.fiscal_period,
        status='posted',
        source='ar_write_off',
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit Bad debt expense
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=write_off.bad_debt_account,
        description=f"Bad debt: {write_off.invoice.invoice_number}",
        debit=write_off.amount,
        credit=Decimal('0.00'),
    )

    # Credit AR account
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=write_off.ar_account,
        description=f"Write-off {write_off.invoice.invoice_number}",
        debit=Decimal('0.00'),
        credit=write_off.amount,
    )

    return je


def calculate_ar_aging_buckets(tenant, as_of_date=None):
    """
    Calculate AR aging buckets grouped by customer.
    Returns: list of dicts with customer info and bucket amounts.
    """
    from .models import Invoice

    if as_of_date is None:
        as_of_date = timezone.now().date()

    invoices = Invoice.unscoped.filter(
        tenant=tenant,
        status__in=['sent', 'partially_paid'],
    ).select_related('customer')

    customer_aging = {}

    for invoice in invoices:
        customer_id = invoice.customer_id
        if customer_id not in customer_aging:
            customer_aging[customer_id] = {
                'customer': invoice.customer,
                'current': Decimal('0.00'),
                '1_30': Decimal('0.00'),
                '31_60': Decimal('0.00'),
                '61_90': Decimal('0.00'),
                '90_plus': Decimal('0.00'),
                'total': Decimal('0.00'),
            }

        balance = invoice.balance_due
        if balance <= Decimal('0.00'):
            continue

        days_overdue = (as_of_date - invoice.due_date).days

        if days_overdue <= 0:
            customer_aging[customer_id]['current'] += balance
        elif days_overdue <= 30:
            customer_aging[customer_id]['1_30'] += balance
        elif days_overdue <= 60:
            customer_aging[customer_id]['31_60'] += balance
        elif days_overdue <= 90:
            customer_aging[customer_id]['61_90'] += balance
        else:
            customer_aging[customer_id]['90_plus'] += balance

        customer_aging[customer_id]['total'] += balance

    return sorted(customer_aging.values(), key=lambda x: x['total'], reverse=True)


def auto_match_receipt(receipt, tenant):
    """
    Automatic cash application: match a receipt to open invoices
    for the same customer using FIFO strategy.
    Returns: list of created ReceiptAllocation objects.
    """
    from .models import Invoice, ReceiptAllocation

    open_invoices = Invoice.unscoped.filter(
        tenant=tenant,
        customer=receipt.customer,
        status__in=['sent', 'partially_paid', 'approved'],
    ).order_by('due_date', 'invoice_date')

    remaining = receipt.amount
    allocations = []

    for invoice in open_invoices:
        if remaining <= Decimal('0.00'):
            break

        balance = invoice.balance_due
        if balance <= Decimal('0.00'):
            continue

        alloc_amount = min(remaining, balance)

        allocation = ReceiptAllocation.objects.create(
            receipt=receipt,
            invoice=invoice,
            amount=alloc_amount,
            discount_given=Decimal('0.00'),
        )
        allocations.append(allocation)
        remaining -= alloc_amount

    return allocations


def get_dunning_candidates(tenant, level=1):
    """
    Find invoices eligible for dunning at the given level.
    Level 1: 1-30 days overdue
    Level 2: 31-60 days overdue
    Level 3: 61-90 days overdue
    Level 4: 90+ days overdue
    """
    from .models import Invoice

    today = timezone.now().date()
    invoices = Invoice.unscoped.filter(
        tenant=tenant,
        status__in=['sent', 'partially_paid'],
    ).select_related('customer')

    level_ranges = {
        1: (1, 30),
        2: (31, 60),
        3: (61, 90),
        4: (91, 9999),
    }
    min_days, max_days = level_ranges.get(level, (1, 30))

    candidates = []
    for invoice in invoices:
        days_overdue = (today - invoice.due_date).days
        if min_days <= days_overdue <= max_days:
            candidates.append({
                'invoice': invoice,
                'customer': invoice.customer,
                'days_overdue': days_overdue,
                'balance_due': invoice.balance_due,
            })

    return sorted(candidates, key=lambda x: x['days_overdue'], reverse=True)


def generate_recurring_invoices(tenant, as_of_date=None):
    """
    Check all active recurring templates and generate invoices
    where next_invoice_date <= as_of_date.
    """
    from dateutil.relativedelta import relativedelta
    from .models import RecurringInvoiceTemplate, Invoice, InvoiceLine

    if as_of_date is None:
        as_of_date = timezone.now().date()

    templates = RecurringInvoiceTemplate.unscoped.filter(
        tenant=tenant,
        status='active',
        next_invoice_date__lte=as_of_date,
    ).select_related('customer', 'payment_term', 'ar_account', 'currency')

    created_invoices = []

    for tmpl in templates:
        # Check occurrence limit
        if tmpl.occurrences_limit > 0 and tmpl.occurrences_created >= tmpl.occurrences_limit:
            tmpl.status = 'completed'
            tmpl.save()
            continue

        # Check end date
        if tmpl.end_date and tmpl.next_invoice_date > tmpl.end_date:
            tmpl.status = 'completed'
            tmpl.save()
            continue

        # Generate invoice
        from apps.company.models import FiscalPeriod
        fiscal_period = FiscalPeriod.unscoped.filter(
            tenant=tenant,
            start_date__lte=tmpl.next_invoice_date,
            end_date__gte=tmpl.next_invoice_date,
            is_closed=False,
        ).first()

        if not fiscal_period:
            continue

        due_days = tmpl.payment_term.due_days if tmpl.payment_term else 30
        due_date = tmpl.next_invoice_date + timedelta(days=due_days)

        invoice = Invoice.unscoped.create(
            tenant=tenant,
            invoice_number=Invoice.generate_invoice_number(tenant),
            customer=tmpl.customer,
            invoice_date=tmpl.next_invoice_date,
            due_date=due_date,
            payment_term=tmpl.payment_term,
            currency=tmpl.currency,
            ar_account=tmpl.ar_account,
            fiscal_period=fiscal_period,
            description=tmpl.description,
            status='approved' if tmpl.auto_send else 'draft',
            sent_date=tmpl.next_invoice_date if tmpl.auto_send else None,
            recurring_template=tmpl,
            created_by=tmpl.created_by,
        )

        # Copy template lines to invoice
        for tmpl_line in tmpl.lines.all():
            InvoiceLine.objects.create(
                invoice=invoice,
                account=tmpl_line.account,
                description=tmpl_line.description,
                quantity=tmpl_line.quantity,
                unit_price=tmpl_line.unit_price,
                amount=tmpl_line.amount,
                tax_amount=tmpl_line.tax_amount,
            )

        invoice.update_totals()
        if tmpl.auto_send:
            invoice.status = 'sent'
        invoice.save()

        created_invoices.append(invoice)

        # Update template
        tmpl.occurrences_created += 1

        # Calculate next date based on frequency
        freq_map = {
            'weekly': relativedelta(weeks=1),
            'biweekly': relativedelta(weeks=2),
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'semiannual': relativedelta(months=6),
            'annual': relativedelta(years=1),
        }
        delta = freq_map.get(tmpl.frequency, relativedelta(months=1))
        tmpl.next_invoice_date = tmpl.next_invoice_date + delta
        tmpl.save()

    return created_invoices


def check_credit_limits(tenant):
    """
    Check all customers against their credit limits.
    Auto-set credit_hold=True if outstanding > limit.
    Returns: list of customers placed on hold.
    """
    from .models import Customer

    customers = Customer.unscoped.filter(
        tenant=tenant,
        is_active=True,
        credit_limit__gt=Decimal('0.00'),
    )

    placed_on_hold = []
    for customer in customers:
        if customer.is_over_credit_limit and not customer.credit_hold:
            customer.credit_hold = True
            customer.credit_hold_reason = 'Auto-hold: Outstanding balance exceeds credit limit'
            customer.save()
            placed_on_hold.append(customer)

    return placed_on_hold


def calculate_bad_debt_provision(tenant, as_of_date=None, rates=None):
    """
    Calculate bad debt provision based on aging.
    Default rates: Current 0%, 1-30 1%, 31-60 3%, 61-90 10%, 90+ 25%
    """
    if rates is None:
        rates = {
            'current': Decimal('0.00'),
            '1_30': Decimal('0.01'),
            '31_60': Decimal('0.03'),
            '61_90': Decimal('0.10'),
            '90_plus': Decimal('0.25'),
        }

    aging_data = calculate_ar_aging_buckets(tenant, as_of_date)

    total_provision = Decimal('0.00')
    breakdown = {
        'current': Decimal('0.00'),
        '1_30': Decimal('0.00'),
        '31_60': Decimal('0.00'),
        '61_90': Decimal('0.00'),
        '90_plus': Decimal('0.00'),
    }

    for entry in aging_data:
        for bucket in breakdown:
            bucket_amount = entry.get(bucket, Decimal('0.00'))
            provision = (bucket_amount * rates[bucket]).quantize(Decimal('0.01'))
            breakdown[bucket] += provision
            total_provision += provision

    return {
        'total_provision': total_provision,
        'breakdown': breakdown,
        'rates': rates,
    }

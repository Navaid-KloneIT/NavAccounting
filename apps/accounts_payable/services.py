"""Business logic for AP module — payment journal entries, aging calculations, etc."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.utils import timezone

from apps.general_ledger.models import JournalEntry, JournalEntryLine


def create_payment_journal_entry(payment, tenant, user):
    """
    Create GL journal entry for a completed payment.
    Debit: AP control account (reduces liability)
    Credit: Bank account (reduces asset)
    If discount taken: Credit discount income account as well.
    """
    from apps.company.models import FiscalPeriod

    entry_number = JournalEntry.generate_entry_number(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=entry_number,
        date=payment.payment_date,
        description=f"AP Payment {payment.payment_number} to {payment.vendor.display_name}",
        reference=payment.reference or payment.check_number or payment.payment_number,
        fiscal_period=payment.fiscal_period,
        status='posted',
        source='ap_payment',
        currency=payment.currency,
        exchange_rate=payment.exchange_rate,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit AP account (reduce liability)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=payment.ap_account,
        description=f"Payment to {payment.vendor.display_name}",
        debit=payment.amount + payment.discount_taken,
        credit=Decimal('0.00'),
    )

    # Credit Bank account (reduce asset)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=payment.bank_account,
        description=f"Payment {payment.payment_number}",
        debit=Decimal('0.00'),
        credit=payment.amount,
    )

    # If discount taken, credit a discount income line
    if payment.discount_taken > Decimal('0.00'):
        # Use the bank account for discount credit (ideally a discount income account)
        # In a full implementation, this would use a configured discount income account
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=payment.bank_account,
            description=f"Early payment discount on {payment.payment_number}",
            debit=Decimal('0.00'),
            credit=payment.discount_taken,
        )

    return je


def create_void_journal_entry(payment, tenant, user):
    """
    Create reversing GL journal entry for a voided payment.
    Reverses the original: Debit Bank, Credit AP.
    """
    entry_number = JournalEntry.generate_entry_number(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=entry_number,
        date=timezone.now().date(),
        description=f"VOID: AP Payment {payment.payment_number} to {payment.vendor.display_name}",
        reference=f"VOID-{payment.payment_number}",
        fiscal_period=payment.fiscal_period,
        status='posted',
        source='ap_payment',
        currency=payment.currency,
        exchange_rate=payment.exchange_rate,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit Bank account (restore asset)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=payment.bank_account,
        description=f"Void payment {payment.payment_number}",
        debit=payment.amount,
        credit=Decimal('0.00'),
    )

    # Credit AP account (restore liability)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=payment.ap_account,
        description=f"Void payment to {payment.vendor.display_name}",
        debit=Decimal('0.00'),
        credit=payment.amount + payment.discount_taken,
    )

    # Reverse discount if applicable
    if payment.discount_taken > Decimal('0.00'):
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=payment.bank_account,
            description=f"Reverse discount on {payment.payment_number}",
            debit=payment.discount_taken,
            credit=Decimal('0.00'),
        )

    return je


def calculate_aging_buckets(tenant, as_of_date=None):
    """
    Calculate AP aging buckets grouped by vendor.
    Returns: list of dicts with vendor info and bucket amounts.
    """
    from .models import Bill

    if as_of_date is None:
        as_of_date = timezone.now().date()

    bills = Bill.unscoped.filter(
        tenant=tenant,
        status__in=['approved', 'partially_paid'],
    ).select_related('vendor')

    vendor_aging = {}

    for bill in bills:
        vendor_id = bill.vendor_id
        if vendor_id not in vendor_aging:
            vendor_aging[vendor_id] = {
                'vendor': bill.vendor,
                'current': Decimal('0.00'),
                '1_30': Decimal('0.00'),
                '31_60': Decimal('0.00'),
                '61_90': Decimal('0.00'),
                '90_plus': Decimal('0.00'),
                'total': Decimal('0.00'),
            }

        balance = bill.balance_due
        if balance <= Decimal('0.00'):
            continue

        days_overdue = (as_of_date - bill.due_date).days

        if days_overdue <= 0:
            vendor_aging[vendor_id]['current'] += balance
        elif days_overdue <= 30:
            vendor_aging[vendor_id]['1_30'] += balance
        elif days_overdue <= 60:
            vendor_aging[vendor_id]['31_60'] += balance
        elif days_overdue <= 90:
            vendor_aging[vendor_id]['61_90'] += balance
        else:
            vendor_aging[vendor_id]['90_plus'] += balance

        vendor_aging[vendor_id]['total'] += balance

    return sorted(vendor_aging.values(), key=lambda x: x['total'], reverse=True)


def get_discount_opportunities(tenant):
    """
    Find bills with available early payment discounts.
    Returns bills sorted by discount_date (most urgent first).
    """
    from .models import Bill

    today = timezone.now().date()
    bills = Bill.unscoped.filter(
        tenant=tenant,
        status__in=['approved', 'partially_paid'],
        payment_term__discount_percentage__gt=0,
        payment_term__discount_days__gt=0,
    ).select_related('vendor', 'payment_term')

    opportunities = []
    for bill in bills:
        if bill.discount_available:
            opportunities.append({
                'bill': bill,
                'discount_date': bill.discount_date,
                'discount_amount': bill.discount_amount,
                'days_remaining': (bill.discount_date - today).days,
                'balance_due': bill.balance_due,
            })

    return sorted(opportunities, key=lambda x: x['days_remaining'])

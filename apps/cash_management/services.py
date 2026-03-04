import csv
import io
import re
import uuid
from decimal import Decimal

from django.db.models import Sum, Q
from django.utils import timezone

from apps.general_ledger.models import JournalEntry, JournalEntryLine


def create_transfer_journal_entry(transfer, tenant, user):
    """
    Create GL journal entry when an intercompany transfer is completed.
    Debit: to_bank_account.gl_account (increase destination)
    Credit: from_bank_account.gl_account (decrease source)
    """
    entry_number = JournalEntry.generate_entry_number(tenant)
    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=entry_number,
        date=transfer.transfer_date,
        description=f"Intercompany Transfer {transfer.transfer_number}: "
                    f"{transfer.from_bank_account} → {transfer.to_bank_account}",
        reference=transfer.transfer_number,
        status='posted',
        source='cm_transfer',
        currency=transfer.currency,
        exchange_rate=transfer.exchange_rate,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit destination account
    JournalEntryLine.unscoped.create(
        journal_entry=je,
        account=transfer.to_bank_account.gl_account,
        description=f"Transfer from {transfer.from_bank_account.bank_name}",
        debit=transfer.amount,
        credit=Decimal('0.00'),
    )

    # Credit source account
    JournalEntryLine.unscoped.create(
        journal_entry=je,
        account=transfer.from_bank_account.gl_account,
        description=f"Transfer to {transfer.to_bank_account.bank_name}",
        debit=Decimal('0.00'),
        credit=transfer.amount,
    )

    return je


def update_bank_account_balance(bank_account):
    """Recompute current_balance from opening_balance + matched transactions."""
    from .models import BankTransaction

    txns = BankTransaction.unscoped.filter(
        bank_account=bank_account, is_matched=True
    )
    credits = txns.filter(transaction_type='credit').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    debits = txns.filter(transaction_type='debit').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    bank_account.current_balance = bank_account.opening_balance + credits - debits
    bank_account.save(update_fields=['current_balance', 'updated_at'])


def run_auto_match(reconciliation):
    """
    Execute auto-match rules against unmatched items in a reconciliation.
    Returns the count of new matches.
    """
    from .models import AutoMatchRule, ReconciliationItem, BankTransaction

    rules = AutoMatchRule.unscoped.filter(
        tenant=reconciliation.tenant, is_active=True
    ).order_by('priority')

    bank_account = reconciliation.bank_account
    gl_account = bank_account.gl_account

    # Get unmatched bank transactions for this account in the period
    unmatched_txns = BankTransaction.unscoped.filter(
        bank_account=bank_account,
        is_matched=False,
        transaction_date__gte=reconciliation.fiscal_period.start_date,
        transaction_date__lte=reconciliation.fiscal_period.end_date,
    )

    # Get unmatched GL entries for this account in the period
    unmatched_gl = JournalEntryLine.objects.filter(
        account=gl_account,
        journal_entry__status='posted',
        journal_entry__date__gte=reconciliation.fiscal_period.start_date,
        journal_entry__date__lte=reconciliation.fiscal_period.end_date,
    ).exclude(
        reconciliation_items__status='matched'
    )

    match_count = 0

    for rule in rules:
        if rule.rule_type == 'exact_amount':
            match_count += _match_by_exact_amount(
                reconciliation, unmatched_txns, unmatched_gl
            )
        elif rule.rule_type == 'reference_match':
            match_count += _match_by_reference(
                reconciliation, unmatched_txns, unmatched_gl, rule.pattern
            )

    return match_count


def _match_by_exact_amount(reconciliation, unmatched_txns, unmatched_gl):
    """Match bank transactions to GL entries by exact amount."""
    from .models import ReconciliationItem

    matched = 0
    for txn in unmatched_txns:
        # Determine the GL amount to match
        if txn.transaction_type == 'debit':
            gl_match = unmatched_gl.filter(credit=txn.amount).first()
        else:
            gl_match = unmatched_gl.filter(debit=txn.amount).first()

        if gl_match:
            ReconciliationItem.objects.create(
                reconciliation=reconciliation,
                bank_transaction=txn,
                journal_entry_line=gl_match,
                match_type='auto',
                status='matched',
                amount=txn.amount,
            )
            txn.is_matched = True
            txn.save(update_fields=['is_matched', 'updated_at'])
            matched += 1

    return matched


def _match_by_reference(reconciliation, unmatched_txns, unmatched_gl, pattern):
    """Match bank transactions to GL entries by reference number."""
    from .models import ReconciliationItem

    matched = 0
    for txn in unmatched_txns:
        if not txn.reference:
            continue
        gl_match = unmatched_gl.filter(
            journal_entry__reference__iexact=txn.reference
        ).first()
        if gl_match:
            amount = txn.amount
            ReconciliationItem.objects.create(
                reconciliation=reconciliation,
                bank_transaction=txn,
                journal_entry_line=gl_match,
                match_type='auto',
                status='matched',
                amount=amount,
            )
            txn.is_matched = True
            txn.save(update_fields=['is_matched', 'updated_at'])
            matched += 1

    return matched


def compute_cash_position(tenant, as_of_date=None):
    """
    Aggregate bank account balances and compute inflows/outflows.
    Returns a list of dicts with account data.
    """
    from .models import BankAccount, BankTransaction

    if as_of_date is None:
        as_of_date = timezone.now().date()

    accounts = BankAccount.unscoped.filter(
        tenant=tenant, is_active=True
    ).select_related('currency', 'gl_account')

    position_data = []
    total_balance = Decimal('0.00')

    for account in accounts:
        txns = BankTransaction.unscoped.filter(
            bank_account=account,
            transaction_date=as_of_date,
        )
        inflows = txns.filter(transaction_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        outflows = txns.filter(transaction_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        position_data.append({
            'account': account,
            'balance': account.current_balance,
            'inflows': inflows,
            'outflows': outflows,
            'net': inflows - outflows,
        })
        total_balance += account.current_balance

    return {
        'accounts': position_data,
        'total_balance': total_balance,
        'as_of_date': as_of_date,
    }


def parse_csv_transactions(file, bank_account, tenant):
    """
    Parse uploaded CSV file and create BankTransaction records.
    Expected columns: Date, Description, Amount, Type (or Debit/Credit columns).
    Returns (created_count, errors).
    """
    from .models import BankTransaction

    batch_id = f"CSV-{uuid.uuid4().hex[:8]}"
    content = file.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content))

    created = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            # Try common CSV column name patterns
            date_str = row.get('Date') or row.get('date') or row.get('Transaction Date', '')
            description = row.get('Description') or row.get('description') or row.get('Memo', '')
            reference = row.get('Reference') or row.get('Check Number') or row.get('reference', '')

            # Handle amount - could be single column or separate debit/credit
            amount_str = row.get('Amount') or row.get('amount', '')
            debit_str = row.get('Debit') or row.get('debit', '')
            credit_str = row.get('Credit') or row.get('credit', '')

            if amount_str:
                amount = Decimal(amount_str.replace(',', '').replace('$', ''))
                txn_type = 'debit' if amount < 0 else 'credit'
                amount = abs(amount)
            elif debit_str or credit_str:
                if debit_str and debit_str.strip():
                    amount = Decimal(debit_str.replace(',', '').replace('$', ''))
                    txn_type = 'debit'
                else:
                    amount = Decimal(credit_str.replace(',', '').replace('$', ''))
                    txn_type = 'credit'
            else:
                errors.append(f"Row {i}: No amount found")
                continue

            # Parse date
            from datetime import datetime
            date_val = None
            for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y'):
                try:
                    date_val = datetime.strptime(date_str.strip(), fmt).date()
                    break
                except (ValueError, AttributeError):
                    continue

            if not date_val:
                errors.append(f"Row {i}: Invalid date '{date_str}'")
                continue

            txn_number = BankTransaction.generate_transaction_number(tenant)
            BankTransaction.unscoped.create(
                tenant=tenant,
                transaction_number=txn_number,
                bank_account=bank_account,
                transaction_date=date_val,
                amount=amount,
                transaction_type=txn_type,
                description=description.strip()[:500],
                reference=str(reference).strip()[:100],
                import_batch=batch_id,
                raw_data=dict(row),
            )
            created += 1

        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    return created, errors


def compute_forecast_variance(forecast):
    """Update variance on all forecast lines where actual_amount is set."""
    lines = forecast.lines.filter(actual_amount__isnull=False)
    for line in lines:
        line.variance = line.actual_amount - line.expected_amount
        line.save(update_fields=['variance'])
    return lines.count()

from decimal import Decimal

from django.utils import timezone

from apps.general_ledger.models import JournalEntry, JournalEntryLine

from .models import (
    EliminationEntry,
    IntercompanyBalance,
    MinorityInterest,
    TranslationAdjustment,
)


def post_ic_transaction(transaction, tenant, user):
    """
    Post an intercompany transaction by creating paired journal entries
    (one for each entity side).
    """
    from apps.company.models import FiscalPeriod

    if transaction.status != 'confirmed':
        raise ValueError('Transaction must be confirmed before posting.')

    from_entity = transaction.from_entity
    to_entity = transaction.to_entity

    # Validate GL accounts exist on both entities
    if not from_entity.ic_receivable_account:
        raise ValueError(f'Entity {from_entity.code} has no IC Receivable account configured.')
    if not to_entity.ic_payable_account:
        raise ValueError(f'Entity {to_entity.code} has no IC Payable account configured.')

    # Create JE for the "from" entity (debit receivable, credit revenue/account)
    from_je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=transaction.date,
        description=f"IC Transaction {transaction.transaction_number} - {from_entity.code} to {to_entity.code}",
        reference=transaction.transaction_number,
        fiscal_period=transaction.fiscal_period,
        status='posted',
        source='me_intercompany',
        currency=transaction.currency,
        exchange_rate=transaction.exchange_rate,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )
    JournalEntryLine.objects.create(
        journal_entry=from_je,
        account=from_entity.ic_receivable_account,
        description=f"IC Receivable from {to_entity.code}",
        debit=transaction.amount,
        credit=Decimal('0.00'),
    )
    JournalEntryLine.objects.create(
        journal_entry=from_je,
        account=to_entity.ic_payable_account,
        description=f"IC Revenue/Transfer to {to_entity.code}",
        debit=Decimal('0.00'),
        credit=transaction.amount,
    )

    # Create JE for the "to" entity (debit expense/account, credit payable)
    to_je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=transaction.date,
        description=f"IC Transaction {transaction.transaction_number} - {to_entity.code} from {from_entity.code}",
        reference=transaction.transaction_number,
        fiscal_period=transaction.fiscal_period,
        status='posted',
        source='me_intercompany',
        currency=transaction.currency,
        exchange_rate=transaction.exchange_rate,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )
    JournalEntryLine.objects.create(
        journal_entry=to_je,
        account=from_entity.ic_receivable_account,
        description=f"IC Expense/Transfer from {from_entity.code}",
        debit=transaction.amount,
        credit=Decimal('0.00'),
    )
    JournalEntryLine.objects.create(
        journal_entry=to_je,
        account=to_entity.ic_payable_account,
        description=f"IC Payable to {from_entity.code}",
        debit=Decimal('0.00'),
        credit=transaction.amount,
    )

    # Update transaction
    transaction.from_journal_entry = from_je
    transaction.to_journal_entry = to_je
    transaction.status = 'posted'
    transaction.save()

    # Update or create IC balance
    balance, created = IntercompanyBalance.unscoped.get_or_create(
        tenant=tenant,
        from_entity=from_entity,
        to_entity=to_entity,
        fiscal_period=transaction.fiscal_period,
        currency=transaction.currency,
        defaults={'balance': Decimal('0.00')},
    )
    balance.balance += transaction.amount
    balance.is_reconciled = False
    balance.save()

    return from_je, to_je


def run_currency_translation(entity, fiscal_period, tenant, user):
    """
    Run currency translation for an entity for a given fiscal period.
    Computes CTA and creates a TranslationAdjustment record.
    """
    from apps.company.models import CompanySettings
    from apps.general_ledger.models import ExchangeRate

    # Determine currencies
    from_currency = entity.functional_currency
    try:
        company_settings = CompanySettings.unscoped.get(tenant=tenant)
        to_currency = company_settings.base_currency
    except CompanySettings.DoesNotExist:
        raise ValueError('Company settings not configured. Set base currency first.')

    if from_currency == to_currency:
        raise ValueError(f'Entity {entity.code} functional currency is same as reporting currency.')

    # Get exchange rate (period end = current rate)
    period_end_rate = ExchangeRate.get_rate(from_currency, to_currency, fiscal_period.end_date, tenant)

    # For now, use period end rate for all translations (simplified)
    # A full implementation would apply different rates per CurrencyTranslationRule
    rate = period_end_rate

    # Create or update translation adjustment
    adj, created = TranslationAdjustment.unscoped.update_or_create(
        tenant=tenant,
        entity=entity,
        fiscal_period=fiscal_period,
        defaults={
            'from_currency': from_currency,
            'to_currency': to_currency,
            'total_assets_translated': Decimal('0.00'),
            'total_liabilities_translated': Decimal('0.00'),
            'total_equity_translated': Decimal('0.00'),
            'total_income_translated': Decimal('0.00'),
            'total_expense_translated': Decimal('0.00'),
            'cta_amount': Decimal('0.00'),
            'cta_cumulative': Decimal('0.00'),
            'calculated_by': user,
        }
    )

    # Get previous period's cumulative CTA
    prev_cta = TranslationAdjustment.unscoped.filter(
        tenant=tenant,
        entity=entity,
        fiscal_period__period_number__lt=fiscal_period.period_number,
    ).order_by('-fiscal_period__period_number').first()

    prev_cumulative = prev_cta.cta_cumulative if prev_cta else Decimal('0.00')
    adj.cta_cumulative = prev_cumulative + adj.cta_amount
    adj.save()

    return adj


def execute_consolidation(consolidation_run, tenant, user):
    """
    Execute a consolidation run: apply elimination rules and compute minority interest.
    """
    consolidation_run.status = 'in_progress'
    consolidation_run.started_at = timezone.now()
    consolidation_run.save()

    try:
        group = consolidation_run.consolidation_group
        fiscal_period = consolidation_run.fiscal_period
        total_elim = Decimal('0.00')
        total_nci = Decimal('0.00')

        # 1. Apply elimination rules
        active_rules = group.elimination_rules.filter(is_active=True, is_auto=True).order_by('priority')

        for rule in active_rules:
            # Get IC balances for entities in the group for this period
            entities = group.entities.all()
            entity_ids = list(entities.values_list('id', flat=True))

            balances = IntercompanyBalance.unscoped.filter(
                tenant=tenant,
                from_entity_id__in=entity_ids,
                to_entity_id__in=entity_ids,
                fiscal_period=fiscal_period,
            )

            for balance in balances:
                if balance.balance == Decimal('0.00'):
                    continue

                amount = abs(balance.balance)

                # Create elimination JE
                je = JournalEntry.unscoped.create(
                    tenant=tenant,
                    entry_number=JournalEntry.generate_entry_number(tenant),
                    date=fiscal_period.end_date,
                    description=f"Elimination: {rule.name} - {balance.from_entity.code}/{balance.to_entity.code}",
                    reference=consolidation_run.run_number,
                    fiscal_period=fiscal_period,
                    status='posted',
                    source='me_elimination',
                    currency=group.reporting_currency,
                    exchange_rate=Decimal('1.00000000'),
                    created_by=user,
                    posted_by=user,
                    posted_at=timezone.now(),
                )
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=rule.debit_account,
                    description=f"Elimination debit - {rule.name}",
                    debit=amount,
                    credit=Decimal('0.00'),
                )
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=rule.credit_account,
                    description=f"Elimination credit - {rule.name}",
                    debit=Decimal('0.00'),
                    credit=amount,
                )

                # Track elimination entry
                EliminationEntry.unscoped.create(
                    tenant=tenant,
                    consolidation_run=consolidation_run,
                    elimination_rule=rule,
                    from_entity=balance.from_entity,
                    to_entity=balance.to_entity,
                    debit_account=rule.debit_account,
                    credit_account=rule.credit_account,
                    amount=amount,
                    description=f"Elimination: {rule.name}",
                    journal_entry=je,
                )

                total_elim += amount

        # 2. Compute minority interest for entities with ownership < 100%
        for entity in group.entities.all():
            if entity.ownership_percentage >= Decimal('100.0000'):
                continue

            minority_pct = entity.minority_percentage
            # Simplified: use zero for now (full implementation would compute from GL balances)
            nci_share = Decimal('0.00')

            MinorityInterest.unscoped.create(
                tenant=tenant,
                consolidation_run=consolidation_run,
                entity=entity,
                fiscal_period=fiscal_period,
                minority_percentage=minority_pct,
                net_income=Decimal('0.00'),
                minority_share=nci_share,
                total_equity=Decimal('0.00'),
                minority_equity=Decimal('0.00'),
            )

            total_nci += nci_share

        # Update run
        consolidation_run.status = 'completed'
        consolidation_run.completed_at = timezone.now()
        consolidation_run.total_eliminations = total_elim
        consolidation_run.total_minority_interest = total_nci
        consolidation_run.save()

    except Exception as e:
        consolidation_run.status = 'failed'
        consolidation_run.error_log = str(e)
        consolidation_run.save()
        raise


def reverse_consolidation(consolidation_run, tenant, user):
    """
    Reverse a completed consolidation run by creating contra journal entries.
    """
    if consolidation_run.status != 'completed':
        raise ValueError('Only completed runs can be reversed.')

    # Reverse each elimination entry's JE
    for elim in consolidation_run.elimination_entries.all():
        if elim.journal_entry:
            # Create contra JE
            contra_je = JournalEntry.unscoped.create(
                tenant=tenant,
                entry_number=JournalEntry.generate_entry_number(tenant),
                date=elim.journal_entry.date,
                description=f"REVERSAL: {elim.journal_entry.description}",
                reference=f"REV-{consolidation_run.run_number}",
                fiscal_period=elim.journal_entry.fiscal_period,
                status='posted',
                source='me_elimination',
                currency=elim.journal_entry.currency,
                exchange_rate=elim.journal_entry.exchange_rate,
                created_by=user,
                posted_by=user,
                posted_at=timezone.now(),
            )
            # Swap debit/credit
            for line in elim.journal_entry.lines.all():
                JournalEntryLine.objects.create(
                    journal_entry=contra_je,
                    account=line.account,
                    description=f"REVERSAL: {line.description}",
                    debit=line.credit,
                    credit=line.debit,
                )

    # Reverse minority interest JEs
    for nci in consolidation_run.minority_interests.all():
        if nci.journal_entry:
            contra_je = JournalEntry.unscoped.create(
                tenant=tenant,
                entry_number=JournalEntry.generate_entry_number(tenant),
                date=nci.journal_entry.date,
                description=f"REVERSAL: {nci.journal_entry.description}",
                reference=f"REV-{consolidation_run.run_number}",
                fiscal_period=nci.journal_entry.fiscal_period,
                status='posted',
                source='me_elimination',
                currency=nci.journal_entry.currency,
                exchange_rate=nci.journal_entry.exchange_rate,
                created_by=user,
                posted_by=user,
                posted_at=timezone.now(),
            )
            for line in nci.journal_entry.lines.all():
                JournalEntryLine.objects.create(
                    journal_entry=contra_je,
                    account=line.account,
                    description=f"REVERSAL: {line.description}",
                    debit=line.credit,
                    credit=line.debit,
                )

    consolidation_run.status = 'reversed'
    consolidation_run.save()


def post_gaap_adjustment(adjustment, tenant, user):
    """
    Post a Local GAAP Adjustment by creating a journal entry.
    """
    if adjustment.status == 'posted':
        raise ValueError('Adjustment is already posted.')

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=adjustment.fiscal_period.end_date,
        description=f"GAAP Adjustment {adjustment.adjustment_number}: {adjustment.description[:100]}",
        reference=adjustment.adjustment_number,
        fiscal_period=adjustment.fiscal_period,
        status='posted',
        source='me_gaap_adjust',
        currency=adjustment.entity.functional_currency,
        exchange_rate=Decimal('1.00000000'),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=adjustment.debit_account,
        description=f"GAAP Adj Debit - {adjustment.from_standard} to {adjustment.to_standard}",
        debit=adjustment.amount,
        credit=Decimal('0.00'),
    )
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=adjustment.credit_account,
        description=f"GAAP Adj Credit - {adjustment.from_standard} to {adjustment.to_standard}",
        debit=Decimal('0.00'),
        credit=adjustment.amount,
    )

    adjustment.journal_entry = je
    adjustment.status = 'posted'
    adjustment.save()

    return je

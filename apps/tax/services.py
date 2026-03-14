from datetime import date
from decimal import Decimal

from django.utils import timezone


def _get_default_currency_id(tenant):
    """Get the default currency for a tenant."""
    from apps.company.models import CompanySettings
    try:
        settings = CompanySettings.unscoped.filter(tenant=tenant).first()
        if settings and settings.default_currency_id:
            return settings.default_currency_id
    except Exception:
        pass
    from apps.company.models import Currency
    currency = Currency.objects.first()
    return currency.id if currency else None


# =============================================================================
# Sales Tax Engine
# =============================================================================

def calculate_combined_rate(tax_group, as_of_date=None):
    """
    Calculate the combined tax rate from all active group members.
    Handles compound rates (calculated on top of base amount + prior taxes).

    Returns: Decimal combined rate percentage.
    """
    if as_of_date is None:
        as_of_date = date.today()

    members = tax_group.members.select_related('tax_rate').filter(
        tax_rate__is_active=True,
        tax_rate__effective_date__lte=as_of_date,
    ).exclude(
        tax_rate__end_date__lt=as_of_date
    ).order_by('priority', 'tax_rate__priority')

    combined = Decimal('0.00000')
    for member in members:
        rate = member.tax_rate
        if rate.is_compound:
            # Compound: rate applies on base + accumulated tax
            combined = combined + rate.rate + (combined * rate.rate / Decimal('100'))
        else:
            combined += rate.rate

    return combined


def calculate_tax_amount(amount, tax_group_or_rate, as_of_date=None, product_category=None):
    """
    Calculate tax on a given amount using a TaxGroup or single TaxRate.

    Args:
        amount: Decimal base amount
        tax_group_or_rate: TaxGroup or TaxRate instance
        as_of_date: Date for rate lookup (defaults to today)
        product_category: Optional product category for rule matching

    Returns: dict with 'tax_amount' and 'breakdown' list
    """
    from .models import TaxGroup, TaxRate, TaxRule

    if as_of_date is None:
        as_of_date = date.today()

    amount = Decimal(str(amount))
    breakdown = []

    if isinstance(tax_group_or_rate, TaxGroup):
        members = tax_group_or_rate.members.select_related(
            'tax_rate', 'tax_rate__jurisdiction'
        ).filter(
            tax_rate__is_active=True,
            tax_rate__effective_date__lte=as_of_date,
        ).exclude(
            tax_rate__end_date__lt=as_of_date
        ).order_by('priority', 'tax_rate__priority')

        running_base = amount
        total_tax = Decimal('0.00')

        for member in members:
            rate = member.tax_rate
            effective_rate = rate.rate

            # Check for product-specific rules
            if product_category:
                rule = TaxRule.objects.filter(
                    jurisdiction=rate.jurisdiction,
                    is_active=True,
                    effective_date__lte=as_of_date,
                    product_category=product_category,
                ).exclude(end_date__lt=as_of_date).first()

                if rule:
                    if rule.rule_type == 'exempt' or rule.rule_type == 'zero_rated':
                        effective_rate = Decimal('0.00000')
                    elif rule.rule_type == 'reduced' and rule.rate_override is not None:
                        effective_rate = rule.rate_override

            if rate.is_compound:
                tax = running_base * effective_rate / Decimal('100')
                running_base += tax
            else:
                tax = amount * effective_rate / Decimal('100')

            tax = tax.quantize(Decimal('0.01'))
            total_tax += tax

            breakdown.append({
                'jurisdiction': rate.jurisdiction.code,
                'jurisdiction_name': rate.jurisdiction.name,
                'rate_name': rate.rate_name,
                'rate': effective_rate,
                'amount': tax,
            })

        return {
            'tax_amount': total_tax,
            'breakdown': breakdown,
        }

    elif isinstance(tax_group_or_rate, TaxRate):
        rate = tax_group_or_rate
        tax = (amount * rate.rate / Decimal('100')).quantize(Decimal('0.01'))
        return {
            'tax_amount': tax,
            'breakdown': [{
                'jurisdiction': rate.jurisdiction.code,
                'jurisdiction_name': rate.jurisdiction.name,
                'rate_name': rate.rate_name,
                'rate': rate.rate,
                'amount': tax,
            }],
        }

    return {'tax_amount': Decimal('0.00'), 'breakdown': []}


# =============================================================================
# Tax Returns
# =============================================================================

def calculate_tax_return(tax_return, tenant):
    """
    Pull amounts from GL for the return period, populate return lines,
    compute totals. Updates status to 'calculated'.
    """
    from apps.general_ledger.models import JournalEntryLine

    # Sum taxable amounts from posted journal entries in the period
    lines = JournalEntryLine.objects.filter(
        journal_entry__tenant=tenant,
        journal_entry__status='posted',
        journal_entry__date__gte=tax_return.period_start,
        journal_entry__date__lte=tax_return.period_end,
    )

    # Calculate totals from existing return lines
    total_taxable = Decimal('0.00')
    total_tax = Decimal('0.00')
    for line in tax_return.lines.all():
        total_taxable += line.taxable_amount
        total_tax += line.tax_amount

    tax_return.total_taxable_amount = total_taxable
    tax_return.total_tax_due = total_tax
    tax_return.net_tax_due = total_tax - tax_return.total_credits
    tax_return.status = 'calculated'
    tax_return.save()


def post_return_payment(payment, tenant, user):
    """
    Create GL journal entry for a tax return payment.
    Debit: Tax Payable, Credit: Cash/Bank.
    """
    from apps.general_ledger.models import JournalEntry, JournalEntryLine

    tax_return = payment.tax_return
    jurisdiction = tax_return.jurisdiction

    # Find a tax payable account from the jurisdiction's rates
    tax_payable_account = None
    rate = jurisdiction.rates.filter(is_active=True).first() if jurisdiction else None
    if rate:
        tax_payable_account = rate.gl_tax_collected_account

    if not tax_payable_account:
        return None

    # Find cash/bank account (first active asset account)
    from apps.general_ledger.models import Account
    cash_account = Account.unscoped.filter(
        tenant=tenant, is_active=True, is_header=False,
        account_type__code__in=['AS', 'ASSET']
    ).first()

    if not cash_account:
        return None

    currency_id = _get_default_currency_id(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=payment.payment_date,
        description=f"Tax Return Payment - {tax_return.return_number}",
        reference=payment.reference,
        fiscal_period=tax_return.fiscal_period,
        status='posted',
        source='tx_return_payment',
        currency_id=currency_id,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit tax payable (reduce liability)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=tax_payable_account,
        debit=payment.amount,
        credit=Decimal('0.00'),
        description=f"Tax payment - {tax_return.return_number}",
    )

    # Credit cash/bank
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=cash_account,
        debit=Decimal('0.00'),
        credit=payment.amount,
        description=f"Tax payment - {tax_return.return_number}",
    )

    payment.gl_journal_entry = je
    payment.save()

    # Update return paid amount
    total_paid = sum(
        p.amount for p in tax_return.payments.all()
    )
    tax_return.amount_paid = total_paid
    tax_return.save()

    return je


# =============================================================================
# Use Tax
# =============================================================================

def accrue_use_tax(assessment, tenant, user):
    """
    Create GL journal entry for use tax accrual.
    Debit: Use Tax Expense, Credit: Use Tax Payable.
    """
    from apps.general_ledger.models import JournalEntry, JournalEntryLine

    currency_id = _get_default_currency_id(tenant)

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=assessment.purchase_date,
        description=f"Use Tax Accrual - {assessment.assessment_number}",
        status='posted',
        source='tx_use_tax',
        currency_id=currency_id,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit expense
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=assessment.gl_expense_account,
        debit=assessment.tax_amount,
        credit=Decimal('0.00'),
        description=f"Use tax - {assessment.vendor}",
    )

    # Credit use tax payable
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=assessment.gl_use_tax_account,
        debit=Decimal('0.00'),
        credit=assessment.tax_amount,
        description=f"Use tax payable - {assessment.vendor}",
    )

    assessment.gl_journal_entry = je
    assessment.status = 'accrued'
    assessment.save()

    return je


def post_use_tax_accrual(accrual, tenant, user):
    """
    Post aggregate use tax accrual GL entry for a period.
    """
    from apps.general_ledger.models import JournalEntry, JournalEntryLine
    from .models import UseTaxAssessment

    # Get all pending assessments for the period
    assessments = UseTaxAssessment.objects.filter(
        tenant=tenant,
        status='pending',
        purchase_date__gte=accrual.period_start,
        purchase_date__lte=accrual.period_end,
    )

    if not assessments.exists():
        return None

    total_purchases = Decimal('0.00')
    total_tax = Decimal('0.00')
    for a in assessments:
        total_purchases += a.purchase_amount
        total_tax += a.tax_amount

    accrual.total_purchases = total_purchases
    accrual.total_tax_accrued = total_tax
    accrual.status = 'posted'
    accrual.save()

    # Accrue each assessment individually
    for a in assessments:
        accrue_use_tax(a, tenant, user)

    return accrual


# =============================================================================
# Income Tax Provision
# =============================================================================

def calculate_provision(provision, tenant):
    """
    Compute current/deferred tax from pretax income, statutory rate,
    and deferred tax items. Updates ETR.
    """
    # Compute tax at statutory rate
    provision.computed_tax = (
        provision.pretax_income * provision.statutory_rate / Decimal('100')
    ).quantize(Decimal('0.01'))

    # Sum temporary differences from deferred items
    total_temp_diff = Decimal('0.00')
    total_deferred = Decimal('0.00')
    for item in provision.deferred_items.all():
        item.temporary_difference = item.book_basis - item.tax_basis
        item.deferred_tax_amount = (
            item.temporary_difference * item.tax_rate / Decimal('100')
        ).quantize(Decimal('0.01'))
        item.save()
        total_temp_diff += item.temporary_difference
        total_deferred += item.deferred_tax_amount

    provision.temporary_differences = total_temp_diff
    provision.deferred_tax_expense = total_deferred
    provision.current_tax_expense = (
        provision.computed_tax + provision.permanent_differences - provision.tax_credits
    ).quantize(Decimal('0.01'))
    provision.total_tax_expense = (
        provision.current_tax_expense + provision.deferred_tax_expense
    ).quantize(Decimal('0.01'))

    # Effective tax rate
    if provision.pretax_income and provision.pretax_income != Decimal('0.00'):
        provision.effective_tax_rate = (
            provision.total_tax_expense / provision.pretax_income * Decimal('100')
        ).quantize(Decimal('0.00001'))
    else:
        provision.effective_tax_rate = Decimal('0.00000')

    provision.status = 'calculated'
    provision.save()


def post_provision(provision, tenant, user):
    """
    Post income tax provision to GL.
    Debit: Income Tax Expense, Credit: Current/Deferred Tax Liability.
    """
    from apps.general_ledger.models import JournalEntry, JournalEntryLine, Account

    currency_id = _get_default_currency_id(tenant)

    # Find expense and liability accounts
    expense_accounts = Account.unscoped.filter(
        tenant=tenant, is_active=True, is_header=False,
        account_type__code__in=['EXP', 'EXPENSE', 'OE']
    )
    liability_accounts = Account.unscoped.filter(
        tenant=tenant, is_active=True, is_header=False,
        account_type__code__in=['LI', 'LIABILITY', 'OL']
    )

    tax_expense_acct = expense_accounts.first()
    tax_liability_acct = liability_accounts.first()

    if not tax_expense_acct or not tax_liability_acct:
        return None

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=timezone.now().date(),
        description=f"Income Tax Provision - {provision.provision_number}",
        fiscal_period=provision.fiscal_period,
        status='posted',
        source='tx_provision',
        currency_id=currency_id,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    if provision.current_tax_expense > 0:
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=tax_expense_acct,
            debit=provision.current_tax_expense,
            credit=Decimal('0.00'),
            description='Current income tax expense',
        )
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=tax_liability_acct,
            debit=Decimal('0.00'),
            credit=provision.current_tax_expense,
            description='Current income tax payable',
        )

    if provision.deferred_tax_expense > 0:
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=tax_expense_acct,
            debit=provision.deferred_tax_expense,
            credit=Decimal('0.00'),
            description='Deferred income tax expense',
        )
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=tax_liability_acct,
            debit=Decimal('0.00'),
            credit=provision.deferred_tax_expense,
            description='Deferred income tax liability',
        )

    provision.gl_journal_entry = je
    provision.status = 'finalized'
    provision.save()

    return je


# =============================================================================
# Tax Calendar
# =============================================================================

def generate_recurring_deadlines(tenant, from_date, to_date):
    """
    Find all recurring TaxDeadline templates and create new instances
    for the specified date range.
    """
    from dateutil.relativedelta import relativedelta
    from .models import TaxDeadline

    templates = TaxDeadline.objects.filter(
        tenant=tenant,
        is_recurring=True,
        recurrence_pattern__in=['monthly', 'quarterly', 'annual'],
    )

    created = []
    for template in templates:
        delta_map = {
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'annual': relativedelta(years=1),
        }
        delta = delta_map[template.recurrence_pattern]
        next_date = template.due_date + delta

        while next_date <= to_date:
            if next_date >= from_date:
                # Check if this deadline already exists
                exists = TaxDeadline.unscoped.filter(
                    tenant=tenant,
                    name=template.name,
                    due_date=next_date,
                ).exists()

                if not exists:
                    new_deadline = TaxDeadline(
                        tenant=tenant,
                        deadline_number=TaxDeadline.generate_deadline_number(tenant),
                        name=template.name,
                        tax_type=template.tax_type,
                        jurisdiction=template.jurisdiction,
                        due_date=next_date,
                        reminder_days=template.reminder_days,
                        status='upcoming',
                        assigned_to=template.assigned_to,
                        is_recurring=False,
                        notes=f"Generated from recurring deadline {template.deadline_number}",
                    )
                    new_deadline.save()
                    created.append(new_deadline)
            next_date += delta

    return created


def check_overdue_deadlines(tenant):
    """Mark overdue deadlines and return list for alert display."""
    from .models import TaxDeadline
    today = date.today()

    overdue = TaxDeadline.objects.filter(
        tenant=tenant,
        status__in=['upcoming', 'in_progress'],
        due_date__lt=today,
    )
    overdue.update(status='overdue')

    return list(TaxDeadline.objects.filter(tenant=tenant, status='overdue'))


# =============================================================================
# Audit Support
# =============================================================================

def post_audit_adjustment(audit, tenant, user):
    """
    Post agreed audit adjustment to GL.
    """
    from apps.general_ledger.models import JournalEntry, JournalEntryLine, Account

    if audit.total_agreed_adjustment == Decimal('0.00'):
        return None

    currency_id = _get_default_currency_id(tenant)

    expense_acct = Account.unscoped.filter(
        tenant=tenant, is_active=True, is_header=False,
        account_type__code__in=['EXP', 'EXPENSE', 'OE']
    ).first()
    liability_acct = Account.unscoped.filter(
        tenant=tenant, is_active=True, is_header=False,
        account_type__code__in=['LI', 'LIABILITY', 'OL']
    ).first()

    if not expense_acct or not liability_acct:
        return None

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=timezone.now().date(),
        description=f"Tax Audit Adjustment - {audit.audit_number}",
        status='posted',
        source='tx_audit_adjust',
        currency_id=currency_id,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    JournalEntryLine.objects.create(
        journal_entry=je,
        account=expense_acct,
        debit=audit.total_agreed_adjustment,
        credit=Decimal('0.00'),
        description=f"Audit adjustment - {audit.audit_number}",
    )

    JournalEntryLine.objects.create(
        journal_entry=je,
        account=liability_acct,
        debit=Decimal('0.00'),
        credit=audit.total_agreed_adjustment,
        description=f"Audit adjustment payable - {audit.audit_number}",
    )

    audit.gl_journal_entry = je
    audit.save()

    return je


# =============================================================================
# Nexus Tracking
# =============================================================================

def update_nexus_thresholds(tenant):
    """
    Recalculate current_period_sales and current_period_transactions
    from activity records.
    """
    from .models import NexusJurisdiction

    nexus_records = NexusJurisdiction.objects.filter(
        tenant=tenant, is_active=True
    )

    for record in nexus_records:
        activities = record.activities.all()
        total_sales = sum(a.sales_amount for a in activities)
        total_transactions = sum(a.transaction_count for a in activities)

        record.current_period_sales = total_sales
        record.current_period_transactions = total_transactions

        # Calculate threshold percentage (use higher of sales/transaction %)
        sales_pct = Decimal('0.00')
        trans_pct = Decimal('0.00')
        if record.economic_threshold_amount > 0:
            sales_pct = (total_sales / record.economic_threshold_amount * 100).quantize(
                Decimal('0.01')
            )
        if record.economic_threshold_transactions > 0:
            trans_pct = Decimal(
                total_transactions / record.economic_threshold_transactions * 100
            ).quantize(Decimal('0.01'))

        record.threshold_percentage = max(sales_pct, trans_pct)

        # Auto-set nexus if threshold exceeded
        if record.threshold_percentage >= Decimal('100.00'):
            record.has_nexus = True

        record.save()


def get_nexus_alerts(tenant):
    """Return list of jurisdictions approaching or exceeding thresholds."""
    from .models import NexusJurisdiction

    alerts = []
    records = NexusJurisdiction.objects.filter(
        tenant=tenant, is_active=True
    ).select_related('jurisdiction')

    for record in records:
        if record.threshold_percentage >= Decimal('100.00'):
            alerts.append({
                'jurisdiction': record.jurisdiction,
                'nexus_type': record.get_nexus_type_display(),
                'level': 'danger',
                'message': f"Nexus threshold exceeded ({record.threshold_percentage}%)",
                'record': record,
            })
        elif record.threshold_percentage >= Decimal('75.00'):
            alerts.append({
                'jurisdiction': record.jurisdiction,
                'nexus_type': record.get_nexus_type_display(),
                'level': 'warning',
                'message': f"Approaching nexus threshold ({record.threshold_percentage}%)",
                'record': record,
            })

    return alerts

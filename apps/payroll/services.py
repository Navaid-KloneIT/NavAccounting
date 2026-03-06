from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone

from apps.general_ledger.models import JournalEntry, JournalEntryLine


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
# Payroll Journal Calculation
# =============================================================================

def calculate_payroll_journal(journal, tenant):
    """
    Calculate gross pay, taxes, benefits, garnishments for all employees
    in the payroll journal. Updates journal line totals.
    """
    from .models import PayrollJournalLine

    total_gross = Decimal('0.00')
    total_deductions = Decimal('0.00')
    total_net = Decimal('0.00')

    for line in journal.lines.select_related('employee'):
        emp = line.employee

        # Calculate gross pay
        if emp.pay_type == 'hourly':
            regular_pay = line.regular_hours * emp.pay_rate
            ot_pay = line.overtime_hours * emp.pay_rate * Decimal('1.5')
            line.overtime_pay = ot_pay.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            line.gross_pay = (regular_pay + ot_pay).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            # Salaried: pay_rate is annual, divide by pay frequency
            divisors = {'weekly': 52, 'biweekly': 26, 'semimonthly': 24, 'monthly': 12}
            divisor = divisors.get(emp.pay_frequency, 26)
            line.gross_pay = (emp.pay_rate / divisor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            line.overtime_pay = Decimal('0.00')

        gross = line.gross_pay

        # Calculate tax withholdings
        withholdings = emp.tax_withholdings.filter(
            end_date__isnull=True, is_employer_paid=False
        )
        line.federal_tax = Decimal('0.00')
        line.state_tax = Decimal('0.00')
        line.local_tax = Decimal('0.00')
        line.social_security = Decimal('0.00')
        line.medicare = Decimal('0.00')

        for wh in withholdings:
            tax_amount = (gross * wh.rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if wh.tax_type == 'federal':
                line.federal_tax = tax_amount
            elif wh.tax_type == 'state':
                line.state_tax = tax_amount
            elif wh.tax_type == 'local':
                line.local_tax = tax_amount
            elif wh.tax_type == 'social_security':
                line.social_security = tax_amount
            elif wh.tax_type == 'medicare':
                line.medicare = tax_amount

        # Calculate benefits deductions
        active_benefits = emp.benefits.filter(is_active=True, end_date__isnull=True)
        line.benefits_deduction = sum(
            b.employee_contribution for b in active_benefits
        ) or Decimal('0.00')

        # Calculate garnishment deductions
        active_garnishments = emp.garnishments.filter(
            status='active'
        ).order_by('priority')
        garnishment_total = Decimal('0.00')
        for g in active_garnishments:
            if g.is_percentage:
                g_amount = (gross * g.amount / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                g_amount = g.amount
            remaining = g.remaining_balance
            if remaining > 0 and g_amount > remaining:
                g_amount = remaining
            garnishment_total += g_amount
        line.garnishment_deduction = garnishment_total

        # Total deductions and net pay
        line.total_deductions = (
            line.federal_tax + line.state_tax + line.local_tax +
            line.social_security + line.medicare +
            line.benefits_deduction + line.garnishment_deduction +
            line.other_deductions
        )
        line.net_pay = line.gross_pay - line.total_deductions
        line.save()

        total_gross += line.gross_pay
        total_deductions += line.total_deductions
        total_net += line.net_pay

    journal.total_gross = total_gross
    journal.total_deductions = total_deductions
    journal.total_net = total_net
    journal.status = 'calculated'
    journal.save()

    return journal


# =============================================================================
# Payroll Journal GL Posting
# =============================================================================

def post_payroll_journal(journal, tenant, user):
    """
    Post a payroll journal to the General Ledger.
    Debit: Salary/Wage Expense accounts (per employee)
    Credit: Payroll Payable / Tax Payable / Benefit Payable accounts
    """
    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=journal.pay_date,
        description=f"Payroll: {journal.journal_number}",
        reference=journal.journal_number,
        status='posted',
        source='pr_payroll',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    line_order = 1
    for line in journal.lines.select_related('employee', 'employee__gl_expense_account'):
        # Debit: Salary Expense
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=line.employee.gl_expense_account,
            description=f"Salary/Wage - {line.employee.full_name}",
            debit=line.gross_pay,
            credit=Decimal('0.00'),
            line_order=line_order,
        )
        line_order += 1

        # Credit: Net Pay (payroll payable)
        if line.net_pay > 0:
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=line.employee.gl_expense_account,
                description=f"Net Pay - {line.employee.full_name}",
                debit=Decimal('0.00'),
                credit=line.net_pay,
                line_order=line_order,
            )
            line_order += 1

        # Credit: Tax withholdings
        total_taxes = (
            line.federal_tax + line.state_tax + line.local_tax +
            line.social_security + line.medicare
        )
        if total_taxes > 0:
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=line.employee.gl_expense_account,
                description=f"Tax Withholdings - {line.employee.full_name}",
                debit=Decimal('0.00'),
                credit=total_taxes,
                line_order=line_order,
            )
            line_order += 1

    journal.gl_journal_entry = je
    journal.status = 'posted'
    journal.save()

    return je


# =============================================================================
# Tax Remittance Posting
# =============================================================================

def post_tax_remittance(remittance, tenant, user):
    """Post a tax remittance payment to GL."""
    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=remittance.paid_date or timezone.now().date(),
        description=f"Tax Remittance: {remittance.remittance_number}",
        reference=remittance.remittance_number,
        status='posted',
        source='pr_tax_remit',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    remittance.gl_journal_entry = je
    remittance.status = 'paid'
    remittance.paid_date = remittance.paid_date or timezone.now().date()
    remittance.save()

    return je


# =============================================================================
# Payroll Reconciliation
# =============================================================================

def perform_reconciliation(reconciliation, tenant):
    """
    Perform gross-to-net reconciliation for a payroll journal.
    Compares journal totals against line-level sums.
    """
    journal = reconciliation.payroll_journal
    lines = journal.lines.all()

    agg = lines.aggregate(
        sum_gross=Sum('gross_pay'),
        sum_taxes=Sum('federal_tax') + Sum('state_tax') + Sum('local_tax') +
                  Sum('social_security') + Sum('medicare'),
        sum_benefits=Sum('benefits_deduction'),
        sum_garnishments=Sum('garnishment_deduction'),
        sum_net=Sum('net_pay'),
    )

    reconciliation.total_gross = agg['sum_gross'] or Decimal('0.00')
    reconciliation.total_taxes = (
        (lines.aggregate(s=Sum('federal_tax'))['s'] or Decimal('0.00')) +
        (lines.aggregate(s=Sum('state_tax'))['s'] or Decimal('0.00')) +
        (lines.aggregate(s=Sum('local_tax'))['s'] or Decimal('0.00')) +
        (lines.aggregate(s=Sum('social_security'))['s'] or Decimal('0.00')) +
        (lines.aggregate(s=Sum('medicare'))['s'] or Decimal('0.00'))
    )
    reconciliation.total_benefits = agg['sum_benefits'] or Decimal('0.00')
    reconciliation.total_garnishments = agg['sum_garnishments'] or Decimal('0.00')
    reconciliation.total_net = agg['sum_net'] or Decimal('0.00')

    expected_net = reconciliation.total_gross - reconciliation.total_taxes - \
                   reconciliation.total_benefits - reconciliation.total_garnishments
    reconciliation.variance_amount = reconciliation.total_net - expected_net

    if reconciliation.variance_amount == Decimal('0.00'):
        reconciliation.status = 'reconciled'
    else:
        reconciliation.status = 'exception'

    reconciliation.save()
    return reconciliation

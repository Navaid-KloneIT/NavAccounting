from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone


def recalculate_budget_total(budget):
    """Recalculate budget total from line items."""
    total = budget.line_items.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    budget.total_amount = total
    budget.save(update_fields=['total_amount', 'updated_at'])
    return budget


def create_budget_version_snapshot(budget, version):
    """Serialize current budget line items into a version snapshot."""
    lines = budget.line_items.select_related('gl_account', 'fiscal_period').all()
    snapshot = []
    for line in lines:
        snapshot.append({
            'gl_account_id': line.gl_account_id,
            'gl_account_number': line.gl_account.account_number,
            'gl_account_name': line.gl_account.name,
            'fiscal_period_id': line.fiscal_period_id,
            'fiscal_period_name': str(line.fiscal_period),
            'department': line.department,
            'amount': str(line.amount),
        })
    version.snapshot_data = snapshot
    version.total_amount = budget.total_amount
    version.save(update_fields=['snapshot_data', 'total_amount', 'updated_at'])
    return version


def calculate_driver_periods(driver):
    """Calculate amounts for all periods of a planning driver."""
    for period in driver.periods.all():
        period.calculated_amount = (
            period.quantity * period.rate
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        period.save(update_fields=['calculated_amount', 'updated_at'])


def generate_variance_analysis(analysis, tenant):
    """Generate variance line items by comparing budget vs actual GL balances."""
    from apps.general_ledger.models import JournalEntryLine

    budget = analysis.budget
    period = analysis.fiscal_period

    budget_lines = budget.line_items.filter(fiscal_period=period).select_related('gl_account')

    analysis.line_items.all().delete()

    total_budget = Decimal('0.00')
    total_actual = Decimal('0.00')

    for bl in budget_lines:
        budget_amt = bl.amount

        actual_amt = JournalEntryLine.unscoped.filter(
            tenant=tenant,
            account=bl.gl_account,
            journal_entry__date__gte=period.start_date,
            journal_entry__date__lte=period.end_date,
            journal_entry__status='posted',
        ).aggregate(
            total=Sum('debit') - Sum('credit')
        )['total'] or Decimal('0.00')

        variance_amt = budget_amt - actual_amt
        variance_pct = Decimal('0.00')
        if budget_amt != 0:
            variance_pct = (
                (variance_amt / budget_amt) * 100
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        from .models import VarianceLineItem
        VarianceLineItem.unscoped.create(
            tenant=tenant,
            analysis=analysis,
            gl_account=bl.gl_account,
            budget_amount=budget_amt,
            actual_amount=actual_amt,
            variance_amount=variance_amt,
            variance_pct=variance_pct,
            is_favorable=variance_amt >= 0,
        )

        total_budget += budget_amt
        total_actual += actual_amt

    analysis.total_budget = total_budget
    analysis.total_actual = total_actual
    analysis.total_variance = total_budget - total_actual
    analysis.status = 'generated'
    analysis.generated_at = timezone.now()
    analysis.save()
    return analysis


def calculate_scenario(scenario, tenant):
    """Apply scenario adjustments to budget line items and produce results."""
    budget = scenario.budget
    results = []

    for adj in scenario.adjustments.select_related('gl_account').all():
        budget_lines = budget.line_items.filter(gl_account=adj.gl_account)
        if adj.fiscal_period:
            budget_lines = budget_lines.filter(fiscal_period=adj.fiscal_period)

        original = budget_lines.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        adj.original_amount = original

        if adj.adjustment_type == 'percentage':
            adj.adjusted_amount = (
                original * (1 + adj.adjustment_value / 100)
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif adj.adjustment_type == 'fixed_amount':
            adj.adjusted_amount = original + adj.adjustment_value
        elif adj.adjustment_type == 'override':
            adj.adjusted_amount = adj.adjustment_value.quantize(Decimal('0.01'))

        adj.save()
        results.append({
            'account': adj.gl_account.account_number,
            'original': str(adj.original_amount),
            'adjusted': str(adj.adjusted_amount),
            'change': str(adj.adjusted_amount - adj.original_amount),
        })

    scenario.result_summary = {'adjustments': results}
    scenario.status = 'calculated'
    scenario.save()
    return scenario


def recalculate_workforce_plan(plan):
    """Recalculate workforce plan totals from positions."""
    positions = plan.positions.all()
    total_headcount = 0
    total_salary = Decimal('0.00')
    total_benefit = Decimal('0.00')

    for pos in positions:
        pos.benefit_amount = (
            pos.annual_salary * pos.benefit_rate / 100 * pos.headcount
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        pos.total_cost = (pos.annual_salary * pos.headcount) + pos.benefit_amount
        pos.save(update_fields=['benefit_amount', 'total_cost', 'updated_at'])

        total_headcount += pos.headcount
        total_salary += pos.annual_salary * pos.headcount
        total_benefit += pos.benefit_amount

    plan.total_headcount = total_headcount
    plan.total_salary_cost = total_salary
    plan.total_benefit_cost = total_benefit
    plan.total_cost = total_salary + total_benefit
    plan.save(update_fields=[
        'total_headcount', 'total_salary_cost', 'total_benefit_cost',
        'total_cost', 'updated_at',
    ])
    return plan

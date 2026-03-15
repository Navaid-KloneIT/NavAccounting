from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone


# =============================================================================
# Financial Statement Generation
# =============================================================================

def generate_balance_sheet(statement):
    """
    Generate balance sheet lines from GL account balances.
    Populates FinancialStatementLine records for assets, liabilities, and equity.
    """
    from apps.general_ledger.models import Account
    from .models import FinancialStatementLine

    accounts = Account.unscoped.filter(
        tenant=statement.tenant, is_active=True,
        account_type__name__in=['Asset', 'Liability', 'Equity']
    ).select_related('account_type').order_by('account_type__name', 'account_number')

    line_order = 0
    current_type_id = None

    for account in accounts:
        # Section header when account type changes
        if account.account_type_id != current_type_id:
            current_type_id = account.account_type_id
            line_order += 1
            FinancialStatementLine.objects.create(
                tenant=statement.tenant,
                statement=statement,
                line_order=line_order,
                line_type='header',
                label=account.account_type.name,
                is_bold=True,
            )

        line_order += 1
        FinancialStatementLine.objects.create(
            tenant=statement.tenant,
            statement=statement,
            line_order=line_order,
            line_type='account',
            label=f"{account.account_number} - {account.name}",
            account=account,
            indent_level=1,
            current_amount=account.balance or Decimal('0.00'),
        )

    statement.status = 'generated'
    statement.generated_at = timezone.now()
    statement.save()


def generate_income_statement(statement):
    """
    Generate income statement lines from revenue and expense accounts.
    """
    from apps.general_ledger.models import Account
    from .models import FinancialStatementLine

    accounts = Account.unscoped.filter(
        tenant=statement.tenant, is_active=True,
        account_type__name__in=['Revenue', 'Expense']
    ).select_related('account_type').order_by('account_type__name', 'account_number')

    line_order = 0
    current_type_id = None

    for account in accounts:
        if account.account_type_id != current_type_id:
            current_type_id = account.account_type_id
            line_order += 1
            FinancialStatementLine.objects.create(
                tenant=statement.tenant,
                statement=statement,
                line_order=line_order,
                line_type='header',
                label=account.account_type.name,
                is_bold=True,
            )

        line_order += 1
        FinancialStatementLine.objects.create(
            tenant=statement.tenant,
            statement=statement,
            line_order=line_order,
            line_type='account',
            label=f"{account.account_number} - {account.name}",
            account=account,
            indent_level=1,
            current_amount=account.balance or Decimal('0.00'),
        )

    statement.status = 'generated'
    statement.generated_at = timezone.now()
    statement.save()


# =============================================================================
# Management Report Variance Calculation
# =============================================================================

def calculate_variance(report):
    """
    Recalculate variance for all lines in a management report.
    """
    for line in report.lines.all():
        line.variance_amount = line.actual_amount - line.budget_amount
        if line.budget_amount and line.budget_amount != Decimal('0'):
            line.variance_percent = (
                (line.variance_amount / abs(line.budget_amount)) * Decimal('100')
            )
        else:
            line.variance_percent = Decimal('0')
        line.is_favorable = line.variance_amount >= Decimal('0')
        line.save()


# =============================================================================
# Consolidation Package Helpers
# =============================================================================

def aggregate_package_entities(package):
    """
    Sum entity-level data for a consolidation package.
    """
    totals = package.entities.filter(
        status__in=['submitted', 'approved']
    ).aggregate(
        total_assets=Sum('total_assets'),
        total_liabilities=Sum('total_liabilities'),
        total_equity=Sum('total_equity'),
        total_revenue=Sum('total_revenue'),
        total_net_income=Sum('net_income'),
    )
    return {k: v or Decimal('0') for k, v in totals.items()}


# =============================================================================
# Dashboard Data Helpers
# =============================================================================

def capture_dashboard_snapshot(dashboard, user=None):
    """
    Capture current state of dashboard widget data as a snapshot.
    """
    from .models import DashboardSnapshot

    widget_data = {}
    for widget in dashboard.widgets.filter(is_visible=True):
        widget_data[str(widget.pk)] = {
            'title': widget.title,
            'widget_type': widget.widget_type,
            'data_source': widget.data_source,
            'config': widget.config_json,
        }

    snapshot = DashboardSnapshot.objects.create(
        tenant=dashboard.tenant,
        dashboard=dashboard,
        snapshot_name=f"Snapshot {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        data_json=widget_data,
        created_by=user,
    )
    return snapshot

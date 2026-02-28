"""Dashboard KPI calculation and data services."""
import random
from decimal import Decimal


def get_kpi_data(tenant):
    """Calculate KPI data for the dashboard."""
    # Placeholder data - will be replaced with real calculations
    # when GL and AR/AP modules are implemented
    return {
        'total_revenue': Decimal('284500.00'),
        'revenue_change': Decimal('12.5'),
        'outstanding_invoices': 23,
        'invoices_amount': Decimal('45200.00'),
        'cash_balance': Decimal('156800.00'),
        'cash_change': Decimal('-3.2'),
        'overdue_payables': 8,
        'payables_amount': Decimal('12400.00'),
    }


def get_cash_flow_data(tenant, months=6):
    """Get cash flow data for chart visualization."""
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    data = {
        'categories': month_names[:months],
        'inflow': [random.randint(20000, 60000) for _ in range(months)],
        'outflow': [random.randint(15000, 45000) for _ in range(months)],
    }
    data['net'] = [
        data['inflow'][i] - data['outflow'][i] for i in range(months)
    ]
    return data


def get_revenue_expense_data(tenant):
    """Get revenue vs expense breakdown."""
    return {
        'revenue_categories': ['Sales', 'Services', 'Interest', 'Other'],
        'revenue_values': [45000, 32000, 5000, 3000],
        'expense_categories': ['Salaries', 'Rent', 'Utilities', 'Marketing', 'Other'],
        'expense_values': [28000, 8000, 3500, 5000, 4500],
    }

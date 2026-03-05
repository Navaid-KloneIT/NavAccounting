import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.tenants.managers import set_current_tenant

from .models import Alert
from .services import (
    get_aging_data,
    get_cash_flow_data,
    get_kpi_data,
    get_module_activity,
    get_quick_actions,
    get_recent_activity,
    get_revenue_expense_data,
)


@login_required
def dashboard_index(request, tenant_slug):
    """Main dashboard view with KPIs, charts, and alerts."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    kpi = get_kpi_data(tenant)
    module_activity = get_module_activity(tenant)
    cash_flow = get_cash_flow_data(tenant)
    monthly_overview = get_revenue_expense_data(tenant)
    aging = get_aging_data(tenant)
    recent_activity = get_recent_activity(tenant)
    quick_actions = get_quick_actions()
    alerts = Alert.objects.filter(tenant=tenant, is_dismissed=False).order_by('-created_at')[:10]

    chart_data = {
        'cashFlow': cash_flow,
        'monthlyOverview': monthly_overview,
        'agingData': aging,
    }

    return render(request, 'dashboard/index.html', {
        'kpi': kpi,
        'module_activity': module_activity,
        'chart_data_json': json.dumps(chart_data),
        'recent_activity': recent_activity,
        'quick_actions': quick_actions,
        'alerts': alerts,
        'nav_active': 'dashboard',
    })

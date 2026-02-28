import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.tenants.managers import set_current_tenant

from .models import Alert
from .services import get_cash_flow_data, get_kpi_data


@login_required
def dashboard_index(request, tenant_slug):
    """Main dashboard view with KPIs, charts, and alerts."""
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')

    set_current_tenant(tenant)

    kpi = get_kpi_data(tenant)
    cash_flow = get_cash_flow_data(tenant)
    alerts = Alert.objects.filter(tenant=tenant, is_dismissed=False).order_by('-created_at')[:10]

    return render(request, 'dashboard/index.html', {
        'kpi': kpi,
        'cash_flow_data': json.dumps(cash_flow),
        'alerts': alerts,
        'nav_active': 'dashboard',
    })

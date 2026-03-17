from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth pages (no tenant required)
    path('auth/', include('apps.accounts.urls_auth')),

    # Tenant selection/switching
    path('tenants/', include('apps.tenants.urls')),

    # Tenant-scoped routes
    path('t/<slug:tenant_slug>/', include([
        path('', include('apps.dashboard.urls')),
        path('company/', include('apps.company.urls')),
        path('users/', include('apps.accounts.urls_users')),
        path('roles/', include('apps.roles.urls')),
        path('gl/', include('apps.general_ledger.urls')),
        path('ap/', include('apps.accounts_payable.urls')),
        path('ar/', include('apps.accounts_receivable.urls')),
        path('cm/', include('apps.cash_management.urls')),
        path('fa/', include('apps.fixed_assets.urls')),
        path('ic/', include('apps.inventory.urls')),
        path('pr/', include('apps.payroll.urls')),
        path('pj/', include('apps.project_costing.urls')),
        path('me/', include('apps.multi_entity.urls')),
        path('tx/', include('apps.tax.urls')),
        path('rc/', include('apps.reporting.urls')),
        path('bp/', include('apps.budgeting.urls')),
        path('au/', include('apps.audit.urls')),
    ])),

    # Vendor Portal (outside tenant scope, token-based auth)
    path('vendor-portal/', include('apps.accounts_payable.urls_portal')),

    # Customer Portal (outside tenant scope, token-based auth)
    path('customer-portal/', include('apps.accounts_receivable.urls_portal')),

    # Root redirect
    path('', include('apps.accounts.urls_root')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        if 'debug_toolbar' in settings.INSTALLED_APPS:
            urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except (ImportError, RuntimeError):
        pass

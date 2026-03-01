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
    ])),

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

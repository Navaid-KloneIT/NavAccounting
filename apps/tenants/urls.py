from django.urls import path

from . import views

app_name = 'tenants'

urlpatterns = [
    path('select/', views.tenant_select, name='select'),
    path('create/', views.tenant_create, name='create'),
    path('switch/<slug:tenant_slug>/', views.tenant_switch, name='switch'),
]

from django.urls import path

from . import views

app_name = 'company'

urlpatterns = [
    path('setup/', views.company_setup, name='setup'),
    path('fiscal-years/', views.fiscal_year_list, name='fiscal_year_list'),
    path('fiscal-years/create/', views.fiscal_year_create, name='fiscal_year_create'),
    path('fiscal-years/<int:pk>/edit/', views.fiscal_year_edit, name='fiscal_year_edit'),
    path('currencies/', views.currency_settings, name='currencies'),
    path('coa-templates/', views.coa_template_list, name='coa_template_list'),
    path('coa-templates/<int:pk>/', views.coa_template_detail, name='coa_template_detail'),
]

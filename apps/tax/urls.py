from django.urls import path

from .views import sales_tax, tax_returns, use_tax, provision, calendar, audit, nexus

app_name = 'tax'

urlpatterns = [
    # =========================================================================
    # Sales Tax Engine — Jurisdictions
    # =========================================================================
    path('jurisdictions/', sales_tax.jurisdiction_list, name='jurisdiction_list'),
    path('jurisdictions/create/', sales_tax.jurisdiction_create, name='jurisdiction_create'),
    path('jurisdictions/<int:pk>/', sales_tax.jurisdiction_detail, name='jurisdiction_detail'),
    path('jurisdictions/<int:pk>/edit/', sales_tax.jurisdiction_edit, name='jurisdiction_edit'),

    # Sales Tax Engine — Tax Rates
    path('tax-rates/', sales_tax.tax_rate_list, name='tax_rate_list'),
    path('tax-rates/create/', sales_tax.tax_rate_create, name='tax_rate_create'),
    path('tax-rates/<int:pk>/edit/', sales_tax.tax_rate_edit, name='tax_rate_edit'),

    # Sales Tax Engine — Tax Rules
    path('tax-rules/', sales_tax.tax_rule_list, name='tax_rule_list'),
    path('tax-rules/create/', sales_tax.tax_rule_create, name='tax_rule_create'),
    path('tax-rules/<int:pk>/edit/', sales_tax.tax_rule_edit, name='tax_rule_edit'),

    # Sales Tax Engine — Tax Groups
    path('tax-groups/', sales_tax.tax_group_list, name='tax_group_list'),
    path('tax-groups/create/', sales_tax.tax_group_create, name='tax_group_create'),
    path('tax-groups/<int:pk>/', sales_tax.tax_group_detail, name='tax_group_detail'),
    path('tax-groups/<int:pk>/edit/', sales_tax.tax_group_edit, name='tax_group_edit'),

    # =========================================================================
    # Tax Returns
    # =========================================================================
    path('returns/', tax_returns.return_list, name='return_list'),
    path('returns/create/', tax_returns.return_create, name='return_create'),
    path('returns/<int:pk>/', tax_returns.return_detail, name='return_detail'),
    path('returns/<int:pk>/edit/', tax_returns.return_edit, name='return_edit'),
    path('returns/<int:pk>/calculate/', tax_returns.return_calculate, name='return_calculate'),
    path('returns/<int:pk>/file/', tax_returns.return_file, name='return_file'),
    path('returns/<int:pk>/payment/', tax_returns.return_payment, name='return_payment'),

    # =========================================================================
    # Use Tax Tracking
    # =========================================================================
    path('use-tax/', use_tax.assessment_list, name='assessment_list'),
    path('use-tax/create/', use_tax.assessment_create, name='assessment_create'),
    path('use-tax/<int:pk>/', use_tax.assessment_detail, name='assessment_detail'),
    path('use-tax/<int:pk>/accrue/', use_tax.assessment_accrue, name='assessment_accrue'),
    path('use-tax/accruals/', use_tax.accrual_list, name='accrual_list'),
    path('use-tax/accruals/create/', use_tax.accrual_create, name='accrual_create'),
    path('use-tax/accruals/<int:pk>/', use_tax.accrual_detail, name='accrual_detail'),
    path('use-tax/accruals/<int:pk>/post/', use_tax.accrual_post, name='accrual_post'),

    # =========================================================================
    # Income Tax Provision
    # =========================================================================
    path('provisions/', provision.provision_list, name='provision_list'),
    path('provisions/create/', provision.provision_create, name='provision_create'),
    path('provisions/<int:pk>/', provision.provision_detail, name='provision_detail'),
    path('provisions/<int:pk>/edit/', provision.provision_edit, name='provision_edit'),
    path('provisions/<int:pk>/calculate/', provision.provision_calculate, name='provision_calculate'),
    path('provisions/<int:pk>/post/', provision.provision_post, name='provision_post'),

    # =========================================================================
    # Tax Calendar
    # =========================================================================
    path('calendar/', calendar.deadline_list, name='deadline_list'),
    path('calendar/create/', calendar.deadline_create, name='deadline_create'),
    path('calendar/<int:pk>/', calendar.deadline_detail, name='deadline_detail'),
    path('calendar/<int:pk>/edit/', calendar.deadline_edit, name='deadline_edit'),
    path('calendar/<int:pk>/complete/', calendar.deadline_complete, name='deadline_complete'),
    path('calendar/generate/', calendar.generate_recurring, name='deadline_generate'),

    # =========================================================================
    # Audit Support
    # =========================================================================
    path('audits/', audit.audit_list, name='audit_list'),
    path('audits/create/', audit.audit_create, name='audit_create'),
    path('audits/<int:pk>/', audit.audit_detail, name='audit_detail'),
    path('audits/<int:pk>/edit/', audit.audit_edit, name='audit_edit'),
    path('audits/<int:pk>/findings/create/', audit.finding_create, name='finding_create'),
    path('audits/<int:pk>/findings/<int:finding_pk>/edit/', audit.finding_edit, name='finding_edit'),
    path('audits/<int:pk>/documents/upload/', audit.document_upload, name='document_upload'),

    # =========================================================================
    # Nexus Tracking
    # =========================================================================
    path('nexus/', nexus.nexus_list, name='nexus_list'),
    path('nexus/create/', nexus.nexus_create, name='nexus_create'),
    path('nexus/dashboard/', nexus.nexus_dashboard, name='nexus_dashboard'),
    path('nexus/<int:pk>/', nexus.nexus_detail, name='nexus_detail'),
    path('nexus/<int:pk>/edit/', nexus.nexus_edit, name='nexus_edit'),
    path('nexus/<int:pk>/activity/create/', nexus.nexus_activity_create, name='nexus_activity_create'),
]

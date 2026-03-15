from django.urls import path

from .views import (
    financial_statements, management_reports, report_builder,
    scheduled_reports, xbrl_filing, statutory_reporting,
    consolidation_reports, dashboards,
)

app_name = 'reporting'

urlpatterns = [
    # =========================================================================
    # Financial Statements
    # =========================================================================
    path('statements/', financial_statements.statement_list, name='statement_list'),
    path('statements/create/', financial_statements.statement_create, name='statement_create'),
    path('statements/<int:pk>/', financial_statements.statement_detail, name='statement_detail'),
    path('statements/<int:pk>/edit/', financial_statements.statement_edit, name='statement_edit'),
    path('statements/<int:pk>/generate/', financial_statements.statement_generate, name='statement_generate'),
    path('statements/<int:pk>/approve/', financial_statements.statement_approve, name='statement_approve'),

    # =========================================================================
    # Management Reports
    # =========================================================================
    path('management/', management_reports.report_list, name='mgmt_report_list'),
    path('management/create/', management_reports.report_create, name='mgmt_report_create'),
    path('management/<int:pk>/', management_reports.report_detail, name='mgmt_report_detail'),
    path('management/<int:pk>/edit/', management_reports.report_edit, name='mgmt_report_edit'),
    path('management/<int:pk>/generate/', management_reports.report_generate, name='mgmt_report_generate'),

    # =========================================================================
    # Custom Report Builder
    # =========================================================================
    path('builder/', report_builder.builder_list, name='builder_list'),
    path('builder/create/', report_builder.builder_create, name='builder_create'),
    path('builder/<int:pk>/', report_builder.builder_detail, name='builder_detail'),
    path('builder/<int:pk>/edit/', report_builder.builder_edit, name='builder_edit'),

    # =========================================================================
    # Scheduled Reports
    # =========================================================================
    path('schedules/', scheduled_reports.schedule_list, name='schedule_list'),
    path('schedules/create/', scheduled_reports.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/', scheduled_reports.schedule_detail, name='schedule_detail'),
    path('schedules/<int:pk>/edit/', scheduled_reports.schedule_edit, name='schedule_edit'),

    # =========================================================================
    # XBRL/EDGAR Filing
    # =========================================================================
    path('xbrl/', xbrl_filing.filing_list, name='filing_list'),
    path('xbrl/create/', xbrl_filing.filing_create, name='filing_create'),
    path('xbrl/<int:pk>/', xbrl_filing.filing_detail, name='filing_detail'),
    path('xbrl/<int:pk>/edit/', xbrl_filing.filing_edit, name='filing_edit'),
    path('xbrl/<int:pk>/validate/', xbrl_filing.filing_validate, name='filing_validate'),
    path('xbrl/<int:pk>/submit/', xbrl_filing.filing_submit, name='filing_submit'),
    path('xbrl/<int:pk>/documents/upload/', xbrl_filing.document_upload, name='filing_document_upload'),

    # =========================================================================
    # Statutory Reporting
    # =========================================================================
    path('statutory/templates/', statutory_reporting.template_list, name='statutory_template_list'),
    path('statutory/templates/create/', statutory_reporting.template_create, name='statutory_template_create'),
    path('statutory/templates/<int:pk>/edit/', statutory_reporting.template_edit, name='statutory_template_edit'),
    path('statutory/', statutory_reporting.statutory_list, name='statutory_list'),
    path('statutory/create/', statutory_reporting.statutory_create, name='statutory_create'),
    path('statutory/<int:pk>/', statutory_reporting.statutory_detail, name='statutory_detail'),
    path('statutory/<int:pk>/edit/', statutory_reporting.statutory_edit, name='statutory_edit'),
    path('statutory/<int:pk>/generate/', statutory_reporting.statutory_generate, name='statutory_generate'),

    # =========================================================================
    # Consolidation Reports
    # =========================================================================
    path('consolidation/', consolidation_reports.package_list, name='package_list'),
    path('consolidation/create/', consolidation_reports.package_create, name='package_create'),
    path('consolidation/<int:pk>/', consolidation_reports.package_detail, name='package_detail'),
    path('consolidation/<int:pk>/edit/', consolidation_reports.package_edit, name='package_edit'),
    path('consolidation/<int:pk>/consolidate/', consolidation_reports.package_consolidate, name='package_consolidate'),

    # =========================================================================
    # Dashboards
    # =========================================================================
    path('dashboards/', dashboards.dashboard_list, name='dashboard_list'),
    path('dashboards/create/', dashboards.dashboard_create, name='dashboard_create'),
    path('dashboards/<int:pk>/', dashboards.dashboard_detail, name='dashboard_detail'),
    path('dashboards/<int:pk>/edit/', dashboards.dashboard_edit, name='dashboard_edit'),
    path('dashboards/<int:pk>/snapshot/', dashboards.snapshot_create, name='dashboard_snapshot_create'),
]

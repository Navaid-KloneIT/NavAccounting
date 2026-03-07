from django.urls import path

from .views import (
    project_setup, time_expense, revenue_recognition,
    project_billing, profitability, resource_planning,
)

app_name = 'project_costing'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------------------
    path('projects/', project_setup.project_list, name='project_list'),
    path('projects/create/', project_setup.project_create, name='project_create'),
    path('projects/<int:pk>/', project_setup.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', project_setup.project_edit, name='project_edit'),

    # -------------------------------------------------------------------------
    # WBS Elements
    # -------------------------------------------------------------------------
    path('projects/<int:project_pk>/wbs/', project_setup.wbs_list, name='wbs_list'),
    path('projects/<int:project_pk>/wbs/create/', project_setup.wbs_create, name='wbs_create'),
    path('projects/<int:project_pk>/wbs/<int:pk>/edit/', project_setup.wbs_edit, name='wbs_edit'),
    path('projects/<int:project_pk>/wbs/<int:pk>/delete/', project_setup.wbs_delete, name='wbs_delete'),

    # -------------------------------------------------------------------------
    # Budgets
    # -------------------------------------------------------------------------
    path('projects/<int:project_pk>/budgets/', project_setup.budget_list, name='budget_list'),
    path('projects/<int:project_pk>/budgets/create/', project_setup.budget_create, name='budget_create'),
    path('projects/<int:project_pk>/budgets/<int:pk>/edit/', project_setup.budget_edit, name='budget_edit'),
    path('projects/<int:project_pk>/budgets/<int:pk>/delete/', project_setup.budget_delete, name='budget_delete'),

    # -------------------------------------------------------------------------
    # Billing Rules
    # -------------------------------------------------------------------------
    path('projects/<int:project_pk>/billing-rules/', project_setup.billing_rule_list, name='billing_rule_list'),
    path('projects/<int:project_pk>/billing-rules/create/', project_setup.billing_rule_create, name='billing_rule_create'),
    path('projects/<int:project_pk>/billing-rules/<int:pk>/edit/', project_setup.billing_rule_edit, name='billing_rule_edit'),
    path('projects/<int:project_pk>/billing-rules/<int:pk>/delete/', project_setup.billing_rule_delete, name='billing_rule_delete'),

    # -------------------------------------------------------------------------
    # Time Entries
    # -------------------------------------------------------------------------
    path('time-entries/', time_expense.time_entry_list, name='time_entry_list'),
    path('time-entries/create/', time_expense.time_entry_create, name='time_entry_create'),
    path('time-entries/<int:pk>/edit/', time_expense.time_entry_edit, name='time_entry_edit'),
    path('time-entries/<int:pk>/delete/', time_expense.time_entry_delete, name='time_entry_delete'),
    path('time-entries/<int:pk>/approve/', time_expense.time_entry_approve, name='time_entry_approve'),

    # -------------------------------------------------------------------------
    # Expenses
    # -------------------------------------------------------------------------
    path('expenses/', time_expense.expense_list, name='expense_list'),
    path('expenses/create/', time_expense.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', time_expense.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', time_expense.expense_delete, name='expense_delete'),

    # -------------------------------------------------------------------------
    # Revenue Recognition
    # -------------------------------------------------------------------------
    path('revenue-recognition/', revenue_recognition.rev_rec_list, name='rev_rec_list'),
    path('revenue-recognition/create/', revenue_recognition.rev_rec_create, name='rev_rec_create'),
    path('revenue-recognition/<int:pk>/', revenue_recognition.rev_rec_detail, name='rev_rec_detail'),
    path('revenue-recognition/<int:pk>/calculate/', revenue_recognition.rev_rec_calculate, name='rev_rec_calculate'),
    path('revenue-recognition/<int:pk>/post/', revenue_recognition.rev_rec_post, name='rev_rec_post'),

    # -------------------------------------------------------------------------
    # Milestones
    # -------------------------------------------------------------------------
    path('projects/<int:project_pk>/milestones/', project_billing.milestone_list, name='milestone_list'),
    path('projects/<int:project_pk>/milestones/create/', project_billing.milestone_create, name='milestone_create'),
    path('projects/<int:project_pk>/milestones/<int:pk>/edit/', project_billing.milestone_edit, name='milestone_edit'),
    path('projects/<int:project_pk>/milestones/<int:pk>/complete/', project_billing.milestone_complete, name='milestone_complete'),

    # -------------------------------------------------------------------------
    # Invoices
    # -------------------------------------------------------------------------
    path('invoices/', project_billing.invoice_list, name='invoice_list'),
    path('invoices/create/', project_billing.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', project_billing.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/approve/', project_billing.invoice_approve, name='invoice_approve'),
    path('invoices/<int:pk>/void/', project_billing.invoice_void, name='invoice_void'),

    # -------------------------------------------------------------------------
    # Profitability
    # -------------------------------------------------------------------------
    path('profitability/', profitability.profitability_dashboard, name='profitability_dashboard'),
    path('profitability/snapshots/', profitability.snapshot_list, name='snapshot_list'),
    path('profitability/<int:project_pk>/', profitability.profitability_detail, name='profitability_detail'),
    path('profitability/<int:project_pk>/snapshot/', profitability.snapshot_create, name='snapshot_create'),

    # -------------------------------------------------------------------------
    # Resource Planning
    # -------------------------------------------------------------------------
    path('resources/', resource_planning.assignment_list, name='assignment_list'),
    path('resources/create/', resource_planning.assignment_create, name='assignment_create'),
    path('resources/<int:pk>/edit/', resource_planning.assignment_edit, name='assignment_edit'),
    path('resources/<int:pk>/delete/', resource_planning.assignment_delete, name='assignment_delete'),
    path('resources/utilization/', resource_planning.utilization_report, name='utilization_report'),
]

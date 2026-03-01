from django.urls import path
from . import views

app_name = 'general_ledger'

urlpatterns = [
    # Chart of Accounts
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),
    path('accounts/import-template/', views.account_import_template, name='account_import_template'),

    # Journal Entries
    path('journal/', views.journal_list, name='journal_list'),
    path('journal/create/', views.journal_create, name='journal_create'),
    path('journal/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journal/<int:pk>/edit/', views.journal_edit, name='journal_edit'),
    path('journal/<int:pk>/submit/', views.journal_submit, name='journal_submit'),
    path('journal/<int:pk>/post/', views.journal_post, name='journal_post'),

    # Journal Approval
    path('approvals/', views.approval_queue, name='approval_queue'),
    path('approvals/<int:pk>/', views.approval_detail, name='approval_detail'),
    path('approvals/<int:pk>/approve/', views.approval_approve, name='approval_approve'),
    path('approvals/<int:pk>/reject/', views.approval_reject, name='approval_reject'),

    # Period Close
    path('period-close/', views.period_close_list, name='period_close_list'),
    path('period-close/<int:pk>/', views.period_close_detail, name='period_close_detail'),
    path('period-close/<int:pk>/close/', views.period_close_action, name='period_close_action'),
    path('period-close/<int:pk>/reopen/', views.period_reopen_action, name='period_reopen_action'),

    # Account Reconciliation
    path('reconciliation/', views.reconciliation_list, name='reconciliation_list'),
    path('reconciliation/create/', views.reconciliation_create, name='reconciliation_create'),
    path('reconciliation/<int:pk>/', views.reconciliation_form, name='reconciliation_form'),

    # Allocation Rules
    path('allocations/', views.allocation_list, name='allocation_list'),
    path('allocations/create/', views.allocation_create, name='allocation_create'),
    path('allocations/<int:pk>/edit/', views.allocation_edit, name='allocation_edit'),
    path('allocations/<int:pk>/run/', views.allocation_run, name='allocation_run'),

    # Audit Trail
    path('audit-trail/', views.audit_list, name='audit_list'),

    # Multi-Currency / Exchange Rates
    path('exchange-rates/', views.exchange_rate_list, name='exchange_rate_list'),
    path('exchange-rates/create/', views.exchange_rate_create, name='exchange_rate_create'),
    path('exchange-rates/<int:pk>/edit/', views.exchange_rate_edit, name='exchange_rate_edit'),
]

from django.urls import path
from . import views

app_name = 'cash_management'

urlpatterns = [
    # --- Bank Account Management ---
    path('bank-accounts/', views.bank_account_list, name='bank_account_list'),
    path('bank-accounts/create/', views.bank_account_create, name='bank_account_create'),
    path('bank-accounts/<int:pk>/', views.bank_account_detail, name='bank_account_detail'),
    path('bank-accounts/<int:pk>/edit/', views.bank_account_edit, name='bank_account_edit'),
    path('bank-accounts/<int:pk>/toggle/', views.bank_account_toggle_active, name='bank_account_toggle_active'),

    # --- Bank Feeds ---
    path('bank-feeds/', views.bank_feed_list, name='bank_feed_list'),
    path('bank-feeds/create/', views.bank_feed_create, name='bank_feed_create'),
    path('bank-feeds/<int:pk>/edit/', views.bank_feed_edit, name='bank_feed_edit'),

    # --- Bank Transactions ---
    path('transactions/', views.bank_transaction_list, name='bank_transaction_list'),
    path('transactions/import/', views.bank_transaction_import, name='bank_transaction_import'),
    path('transactions/<int:pk>/', views.bank_transaction_detail, name='bank_transaction_detail'),

    # --- Reconciliation ---
    path('reconciliation/', views.reconciliation_list, name='reconciliation_list'),
    path('reconciliation/start/', views.reconciliation_start, name='reconciliation_start'),
    path('reconciliation/<int:pk>/', views.reconciliation_workspace, name='reconciliation_workspace'),
    path('reconciliation/<int:pk>/match/', views.reconciliation_match, name='reconciliation_match'),
    path('reconciliation/<int:pk>/unmatch/', views.reconciliation_unmatch, name='reconciliation_unmatch'),
    path('reconciliation/<int:pk>/auto-match/', views.reconciliation_auto_match, name='reconciliation_auto_match'),
    path('reconciliation/<int:pk>/complete/', views.reconciliation_complete, name='reconciliation_complete'),
    path('match-rules/', views.auto_match_rule_list, name='auto_match_rule_list'),
    path('match-rules/create/', views.auto_match_rule_create, name='auto_match_rule_create'),
    path('match-rules/<int:pk>/edit/', views.auto_match_rule_edit, name='auto_match_rule_edit'),

    # --- Cash Positioning ---
    path('cash-position/', views.cash_position_dashboard, name='cash_position_dashboard'),

    # --- Treasury Forecasting ---
    path('forecasts/', views.forecast_list, name='forecast_list'),
    path('forecasts/create/', views.forecast_create, name='forecast_create'),
    path('forecasts/<int:pk>/', views.forecast_detail, name='forecast_detail'),
    path('forecasts/<int:pk>/edit/', views.forecast_edit, name='forecast_edit'),

    # --- Inter-company Transfers ---
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/create/', views.transfer_create, name='transfer_create'),
    path('transfers/<int:pk>/', views.transfer_detail, name='transfer_detail'),
    path('transfers/<int:pk>/approve/', views.transfer_approve, name='transfer_approve'),
    path('transfers/<int:pk>/complete/', views.transfer_complete, name='transfer_complete'),
    path('transfers/<int:pk>/cancel/', views.transfer_cancel, name='transfer_cancel'),

    # --- Bank Fee Analysis ---
    path('bank-fees/', views.bank_fee_list, name='bank_fee_list'),
    path('bank-fees/create/', views.bank_fee_create, name='bank_fee_create'),
    path('bank-fees/<int:pk>/edit/', views.bank_fee_edit, name='bank_fee_edit'),
    path('bank-fees/analysis/', views.bank_fee_analysis, name='bank_fee_analysis'),
]

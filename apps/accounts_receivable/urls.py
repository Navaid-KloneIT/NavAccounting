from django.urls import path
from . import views

app_name = 'accounts_receivable'

urlpatterns = [
    # Customer Management
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/toggle/', views.customer_toggle_active, name='customer_toggle_active'),
    path('customers/<int:pk>/credit-hold/', views.customer_credit_hold, name='customer_credit_hold'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/submit/', views.invoice_submit, name='invoice_submit'),
    path('invoices/<int:pk>/send/', views.invoice_send, name='invoice_send'),
    path('invoices/<int:pk>/void/', views.invoice_void, name='invoice_void'),
    path('invoices/approvals/', views.invoice_approval_queue, name='invoice_approval_queue'),
    path('invoices/approvals/<int:pk>/approve/', views.invoice_approve, name='invoice_approve'),
    path('invoices/approvals/<int:pk>/reject/', views.invoice_reject, name='invoice_reject'),

    # Recurring Invoicing
    path('recurring/', views.recurring_list, name='recurring_list'),
    path('recurring/create/', views.recurring_create, name='recurring_create'),
    path('recurring/<int:pk>/', views.recurring_detail, name='recurring_detail'),
    path('recurring/<int:pk>/edit/', views.recurring_edit, name='recurring_edit'),
    path('recurring/<int:pk>/pause/', views.recurring_pause, name='recurring_pause'),
    path('recurring/<int:pk>/cancel/', views.recurring_cancel, name='recurring_cancel'),
    path('recurring/<int:pk>/generate/', views.recurring_generate, name='recurring_generate'),

    # Receipts (Payment Collection)
    path('receipts/', views.receipt_list, name='receipt_list'),
    path('receipts/create/', views.receipt_create, name='receipt_create'),
    path('receipts/<int:pk>/', views.receipt_detail, name='receipt_detail'),
    path('receipts/<int:pk>/complete/', views.receipt_complete, name='receipt_complete'),
    path('receipts/<int:pk>/void/', views.receipt_void, name='receipt_void'),

    # Credit Memos
    path('credit-memos/', views.credit_memo_list, name='credit_memo_list'),
    path('credit-memos/create/', views.credit_memo_create, name='credit_memo_create'),
    path('credit-memos/<int:pk>/', views.credit_memo_detail, name='credit_memo_detail'),
    path('credit-memos/<int:pk>/approve/', views.credit_memo_approve, name='credit_memo_approve'),

    # Cash Application
    path('cash-application/', views.cash_application, name='cash_application'),
    path('cash-application/<int:pk>/auto-match/', views.cash_application_auto_match, name='cash_application_auto_match'),

    # Collections
    path('collections/', views.collections_dashboard, name='collections_dashboard'),
    path('collections/activities/', views.collection_activity_list, name='collection_activity_list'),
    path('collections/<int:pk>/', views.collection_customer_detail, name='collection_customer_detail'),
    path('collections/<int:pk>/add-activity/', views.collection_add_activity, name='collection_add_activity'),

    # Write-Offs
    path('invoices/<int:pk>/write-off/', views.write_off_create, name='write_off_create'),
    path('write-offs/<int:pk>/approve/', views.write_off_approve, name='write_off_approve'),

    # Aging Reports
    path('reports/aging/', views.ar_aging_summary, name='ar_aging_summary'),
    path('reports/aging/export/', views.ar_aging_export, name='ar_aging_export'),
    path('reports/aging/<int:customer_pk>/', views.ar_aging_detail, name='ar_aging_detail'),
]

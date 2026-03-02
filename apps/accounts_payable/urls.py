from django.urls import path
from . import views

app_name = 'accounts_payable'

urlpatterns = [
    # Vendor Management
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('vendors/<int:pk>/edit/', views.vendor_edit, name='vendor_edit'),
    path('vendors/<int:pk>/toggle/', views.vendor_toggle_active, name='vendor_toggle_active'),

    # Payment Terms
    path('payment-terms/', views.payment_term_list, name='payment_term_list'),
    path('payment-terms/create/', views.payment_term_create, name='payment_term_create'),
    path('payment-terms/<int:pk>/edit/', views.payment_term_edit, name='payment_term_edit'),

    # Bill Processing
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/create/', views.bill_create, name='bill_create'),
    path('bills/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('bills/<int:pk>/edit/', views.bill_edit, name='bill_edit'),
    path('bills/<int:pk>/submit/', views.bill_submit, name='bill_submit'),
    path('bills/<int:pk>/void/', views.bill_void, name='bill_void'),
    path('bills/approvals/', views.bill_approval_queue, name='bill_approval_queue'),
    path('bills/<int:pk>/approve/', views.bill_approve, name='bill_approve'),
    path('bills/<int:pk>/reject/', views.bill_reject, name='bill_reject'),

    # Payment Processing
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/complete/', views.payment_complete, name='payment_complete'),
    path('payments/<int:pk>/void/', views.payment_void, name='payment_void'),

    # Payment Batches
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:pk>/process/', views.batch_process, name='batch_process'),

    # Bill Capture / Uploads
    path('uploads/', views.bill_upload_list, name='bill_upload_list'),
    path('uploads/create/', views.bill_upload_create, name='bill_upload_create'),
    path('uploads/<int:pk>/', views.bill_upload_detail, name='bill_upload_detail'),
    path('uploads/<int:pk>/create-bill/', views.bill_upload_create_bill, name='bill_upload_create_bill'),

    # Payment Scheduling
    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedule/<int:pk>/execute/', views.schedule_execute, name='schedule_execute'),
    path('schedule/<int:pk>/cancel/', views.schedule_cancel, name='schedule_cancel'),

    # Aging Reports
    path('reports/aging/', views.aging_summary, name='aging_summary'),
    path('reports/aging/<int:vendor_pk>/', views.aging_detail, name='aging_detail'),
    path('reports/aging/export/', views.aging_export, name='aging_export'),

    # Early Payment Discounts
    path('reports/discounts/', views.discount_opportunities, name='discount_opportunities'),
]

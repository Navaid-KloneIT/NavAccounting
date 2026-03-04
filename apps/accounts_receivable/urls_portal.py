from django.urls import path
from . import views_portal

app_name = 'customer_portal'

urlpatterns = [
    path('login/', views_portal.portal_login, name='portal_login'),
    path('dashboard/', views_portal.portal_dashboard, name='portal_dashboard'),
    path('invoices/', views_portal.portal_invoice_list, name='portal_invoice_list'),
    path('invoices/<int:pk>/', views_portal.portal_invoice_detail, name='portal_invoice_detail'),
    path('invoices/<int:pk>/pay/', views_portal.portal_make_payment, name='portal_make_payment'),
    path('messages/', views_portal.portal_messages, name='portal_messages'),
    path('messages/<int:pk>/', views_portal.portal_message_detail, name='portal_message_detail'),
    path('logout/', views_portal.portal_logout, name='portal_logout'),
]

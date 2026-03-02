from django.urls import path
from . import views_portal

app_name = 'vendor_portal'

urlpatterns = [
    path('login/', views_portal.portal_login, name='portal_login'),
    path('dashboard/', views_portal.portal_dashboard, name='portal_dashboard'),
    path('bills/<int:pk>/', views_portal.portal_bill_detail, name='portal_bill_detail'),
    path('messages/', views_portal.portal_messages, name='portal_messages'),
    path('messages/<int:pk>/', views_portal.portal_message_detail, name='portal_message_detail'),
    path('logout/', views_portal.portal_logout, name='portal_logout'),
]

from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='account_login'),
    path('register/', views.CustomSignupView.as_view(), name='account_signup'),
    path('forgot-password/', views.CustomPasswordResetView.as_view(), name='account_reset_password'),
    path('password/reset/key/<str:uidb36>-<str:key>/',
         views.CustomPasswordResetFromKeyView.as_view(),
         name='account_reset_password_from_key'),
    path('logout/', views.custom_logout, name='account_logout'),
    path('confirm-email/', views.email_verification_sent, name='account_email_verification_sent'),
    path('confirm-email/<str:key>/', views.CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    path('accept-invite/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
]

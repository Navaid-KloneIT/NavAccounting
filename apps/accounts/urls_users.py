from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('invite/', views.user_invite, name='user_invite'),
    path('profile/', views.user_profile, name='profile'),
]

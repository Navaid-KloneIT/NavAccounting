from django.urls import path

from . import views

app_name = 'roles'

urlpatterns = [
    path('', views.role_list, name='list'),
    path('create/', views.role_create, name='create'),
    path('<int:pk>/edit/', views.role_edit, name='edit'),
    path('assign/', views.role_assign, name='assign'),
]

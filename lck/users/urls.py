from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('change-password/', views.change_password, name='change_password'),
    path('users/edit/<int:user_id>/', views.user_edit, name='user_edit'),
    path('users/create/', views.user_create, name='user_create'),
]
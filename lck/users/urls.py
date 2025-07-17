from django.urls import path
from . import views

urlpatterns = [
    # Login and logout
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Password change
    path('change-password/', views.change_password, name='change_password'),
    
    # User management (admin only)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/edit/<int:user_id>/', views.user_edit, name='user_edit'),

    path('debug-permissions/', views.debug_permissions, name='debug_permissions'),
]
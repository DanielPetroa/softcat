from django.urls import path
from . import views

urlpatterns = [
    # Lista y búsqueda de clientes
    path('', views.client_list, name='client_list'),
    
    # Detalle de cliente
    path('<int:pk>/', views.client_detail, name='client_detail'),
    
    # Crear nuevo cliente
    path('create/', views.client_create, name='client_create'),
    
    # Editar cliente
    path('<int:pk>/edit/', views.client_edit, name='client_edit'),
    
    # Eliminar cliente (soft delete)
    path('<int:pk>/delete/', views.client_delete, name='client_delete'),
    
    # Reactivar cliente
    path('<int:pk>/activate/', views.client_activate, name='client_activate'),
]
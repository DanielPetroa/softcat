from django.urls import path
from . import views

urlpatterns = [
    # Lista y búsqueda de geometrías
    path('', views.geometry_list, name='geometry_list'),
    
    # Vista de mapa general
    path('map/', views.geometry_map_view, name='geometry_map_view'),
    
    # Detalle de geometría (con mapa)
    path('<int:pk>/', views.geometry_detail, name='geometry_detail'),
    
    # Crear nueva geometría
    path('create/', views.geometry_create, name='geometry_create'),
    
    # Editar geometría
    path('<int:pk>/edit/', views.geometry_edit, name='geometry_edit'),
    
    # Eliminar geometría
    path('<int:pk>/delete/', views.geometry_delete, name='geometry_delete'),
    
    # Toggle monitoreo
    path('<int:pk>/toggle-monitoring/', views.geometry_toggle_monitoring, name='geometry_toggle_monitoring'),
    
    # Validación AJAX de GeoJSON
    path('validate-geojson/', views.geometry_validate_geojson, name='geometry_validate_geojson'),
]
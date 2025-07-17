from django.urls import path
from . import views

urlpatterns = [
    # Payout CRUD operations
    path('', views.payout_list, name='payout_list'),
    path('create/', views.payout_create, name='payout_create'),
    path('<int:pk>/', views.payout_detail, name='payout_detail'),
    path('<int:pk>/edit/', views.payout_edit, name='payout_edit'),
    path('<int:pk>/delete/', views.payout_delete, name='payout_delete'),
    path('<int:pk>/activate/', views.payout_activate, name='payout_activate'),
    path('<int:pk>/duplicate/', views.payout_duplicate, name='payout_duplicate'),
    
    # Geometry-specific payout views
    path('geometry/<int:geometry_id>/', views.payout_by_geometry, name='payout_by_geometry'),
]
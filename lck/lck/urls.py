from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login')),
    path('', include('users.urls')),
    path('clients/', include('clients.urls')),
    path('geometries/', include('geometries.urls')),
]

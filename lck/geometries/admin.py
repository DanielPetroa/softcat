from django.contrib import admin
from .models import Geometria

@admin.register(Geometria)
class GeometriaAdmin(admin.ModelAdmin):
    list_display = ['id_geometria', 'nombre', 'id_cliente', 'geometry_type', 'monitoreo_activo', 'creado_en']
    list_filter = ['monitoreo_activo', 'creado_en', 'id_cliente']
    search_fields = ['nombre', 'id_cliente__nombre']
    readonly_fields = ['creado_en']
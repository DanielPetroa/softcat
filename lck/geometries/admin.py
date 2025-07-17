from django.contrib import admin
from django.utils.html import format_html
from .models import Geometria

@admin.register(Geometria)
class GeometriaAdmin(admin.ModelAdmin):
    list_display = [
        'id_geometria', 
        'nombre', 
        'id_cliente', 
        'geometry_type_display', 
        'coordinates_summary_short',
        'monitoreo_status',
        'creado_en'
    ]
    list_filter = [
        'monitoreo_activo', 
        'creado_en', 
        'id_cliente__sector',
        'id_cliente__pais'
    ]
    search_fields = [
        'nombre', 
        'id_cliente__nombre',
        'id_cliente__contacto_principal'
    ]
    readonly_fields = [
        'creado_en', 
        'geometry_type_display',
        'coordinates_summary',
        'bounds_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('nombre', 'id_cliente', 'monitoreo_activo')
        }),
        ('Geometry Data', {
            'fields': ('geojson', 'geometry_type_display', 'coordinates_summary'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('creado_en', 'bounds_display'),
            'classes': ('collapse',)
        }),
    )
    
    # Filtros personalizados
    list_per_page = 25
    date_hierarchy = 'creado_en'
    
    def geometry_type_display(self, obj):
        """Mostrar tipo de geometría con icono"""
        geometry_type = obj.geometry_type
        icon_map = {
            'Point': '📍',
            'Polygon': '⬢',
            'LineString': '📈',
            'MultiPoint': '📍📍',
            'MultiPolygon': '⬢⬢',
            'MultiLineString': '📈📈',
        }
        icon = icon_map.get(geometry_type, '🗺️')
        return format_html(f'{icon} {geometry_type}')
    geometry_type_display.short_description = 'Geometry Type'
    
    def coordinates_summary_short(self, obj):
        """Resumen corto de coordenadas para lista"""
        summary = obj.coordinates_summary
        if len(summary) > 30:
            return summary[:27] + '...'
        return summary
    coordinates_summary_short.short_description = 'Coordinates'
    
    def monitoreo_status(self, obj):
        """Estado de monitoreo con colores"""
        if obj.monitoreo_activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">● Inactive</span>'
            )
    monitoreo_status.short_description = 'Monitoring'
    
    def bounds_display(self, obj):
        """Mostrar bounds de la geometría"""
        bounds = obj.bounds
        if bounds:
            return format_html(
                '<strong>Center:</strong> {:.4f}, {:.4f}<br>'
                '<strong>Bounds:</strong> [{:.4f}, {:.4f}] to [{:.4f}, {:.4f}]',
                bounds['center_lat'], bounds['center_lng'],
                bounds['min_lat'], bounds['min_lng'],
                bounds['max_lat'], bounds['max_lng']
            )
        return 'No bounds available'
    bounds_display.short_description = 'Geographic Bounds'
    
    # Acciones personalizadas
    actions = ['activate_monitoring', 'deactivate_monitoring']
    
    def activate_monitoring(self, request, queryset):
        """Activar monitoreo para geometrías seleccionadas"""
        updated = queryset.update(monitoreo_activo=True)
        self.message_user(
            request,
            f'{updated} geometries had their monitoring activated.'
        )
    activate_monitoring.short_description = "Activate monitoring for selected geometries"
    
    def deactivate_monitoring(self, request, queryset):
        """Desactivar monitoreo para geometrías seleccionadas"""
        updated = queryset.update(monitoreo_activo=False)
        self.message_user(
            request,
            f'{updated} geometries had their monitoring deactivated.'
        )
    deactivate_monitoring.short_description = "Deactivate monitoring for selected geometries"
    
    # Personalizar formulario
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personalizar campo de cliente"""
        if db_field.name == "id_cliente":
            kwargs["queryset"] = db_field.related_model.objects.filter(activo=True).order_by('nombre')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('id_cliente')
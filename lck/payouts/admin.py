from django.contrib import admin
from .models import PayoutOption

@admin.register(PayoutOption)
class PayoutOptionAdmin(admin.ModelAdmin):
    list_display = [
        'id_payout_option',
        'get_geometry_name',
        'get_client_name',
        'trigger_type',
        'int_var',
        'int_val1',
        'int_val2',
        'payout_percent_limit1',
        'payout_percent_limit2',
        'payout_method_by_geom',
        'activo',
        'creado_en'
    ]
    
    list_filter = [
        'activo',
        'trigger_type',
        'payout_method_by_geom',
        'creado_en',
        'id_geometria__id_cliente__nombre',
        'id_geometria__id_cliente__pais'
    ]
    
    search_fields = [
        'id_geometria__nombre',
        'id_geometria__id_cliente__nombre',
        'trigger_type',
        'int_var',
        'payout_method_by_geom'
    ]
    
    list_editable = ['activo']
    
    readonly_fields = ['id_payout_option', 'creado_en', 'actualizado_en']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id_payout_option', 'id_geometria', 'activo')
        }),
        ('Trigger Configuration', {
            'fields': ('trigger_type', 'int_var', 'int_val1', 'int_val2'),
            'description': 'Configure when this payout should be triggered'
        }),
        ('Filter Configuration', {
            'fields': ('filter_var', 'filter_value', 'filter_condition'),
            'description': 'Optional additional filtering conditions',
            'classes': ('collapse',)
        }),
        ('Payout Configuration', {
            'fields': ('payout_percent_limit1', 'payout_percent_limit2', 'payout_method_by_geom'),
            'description': 'Configure payout amounts and calculation method'
        }),
        ('Timestamps', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        })
    )
    
    def get_geometry_name(self, obj):
        return obj.id_geometria.nombre
    get_geometry_name.short_description = 'Geometry'
    get_geometry_name.admin_order_field = 'id_geometria__nombre'
    
    def get_client_name(self, obj):
        return obj.id_geometria.id_cliente.nombre
    get_client_name.short_description = 'Client'
    get_client_name.admin_order_field = 'id_geometria__id_cliente__nombre'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'id_geometria',
            'id_geometria__id_cliente'
        )
    
    # Custom actions
    actions = ['activate_payouts', 'deactivate_payouts']
    
    def activate_payouts(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} payout options were activated.')
    activate_payouts.short_description = 'Activate selected payout options'
    
    def deactivate_payouts(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} payout options were deactivated.')
    deactivate_payouts.short_description = 'Deactivate selected payout options'
from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'pais', 'contacto_principal', 'activo', 'creado_en')
    list_filter = ('activo', 'pais', 'tipo')
    search_fields = ('nombre', 'contacto_principal', 'correo_principal')
    readonly_fields = ('creado_en',)
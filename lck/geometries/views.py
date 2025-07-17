from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import Geometria
from .forms import GeometriaForm
from clients.models import Cliente

def admin_required(view_func):
    """Decorator para requerir rol de admin"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@admin_required
def geometry_list(request):
    """Lista de geometrías con búsqueda y filtros"""
    query = request.GET.get('q', '')
    cliente_filter = request.GET.get('cliente', '')
    tipo_filter = request.GET.get('tipo', '')
    monitoreo_filter = request.GET.get('monitoreo', '')
    
    geometrias = Geometria.objects.select_related('id_cliente').all().order_by('-creado_en')
    
    # Aplicar filtros de búsqueda
    if query:
        geometrias = geometrias.filter(
            Q(nombre__icontains=query) |
            Q(id_cliente__nombre__icontains=query)
        )
    
    if cliente_filter:
        geometrias = geometrias.filter(id_cliente_id=cliente_filter)
    
    if tipo_filter:
        # Filtrar por tipo de geometría almacenado en el GeoJSON
        geometrias = geometrias.filter(geojson__type=tipo_filter)
        
    if monitoreo_filter:
        if monitoreo_filter == 'true':
            geometrias = geometrias.filter(monitoreo_activo=True)
        elif monitoreo_filter == 'false':
            geometrias = geometrias.filter(monitoreo_activo=False)
    
    # Obtener listas para filtros
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    
    # Obtener tipos de geometría únicos
    tipos_geometria = []
    for geom in Geometria.objects.exclude(geojson__isnull=True):
        if geom.geojson and 'type' in geom.geojson:
            tipos_geometria.append(geom.geojson['type'])
    tipos_geometria = list(set(tipos_geometria))  # Eliminar duplicados
    
    # Paginación
    paginator = Paginator(geometrias, 10)  # 10 geometrías por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_geometrias = Geometria.objects.count()
    geometrias_activas = Geometria.objects.filter(monitoreo_activo=True).count()
    geometrias_inactivas = Geometria.objects.filter(monitoreo_activo=False).count()
    
    # Estadísticas por cliente
    clientes_con_geometrias = Cliente.objects.annotate(
        num_geometrias=Count('geometrias')
    ).filter(num_geometrias__gt=0).count()
    
    context = {
        'geometrias': page_obj,
        'query': query,
        'cliente_filter': cliente_filter,
        'tipo_filter': tipo_filter,
        'monitoreo_filter': monitoreo_filter,
        'clientes': clientes,
        'tipos_geometria': tipos_geometria,
        'total_geometrias': total_geometrias,
        'geometrias_activas': geometrias_activas,
        'geometrias_inactivas': geometrias_inactivas,
        'clientes_con_geometrias': clientes_con_geometrias,
    }
    
    return render(request, 'geometries/geometry_list.html', context)

@login_required
@admin_required
def geometry_detail(request, pk):
    """Detalle de una geometría específica con mapa"""
    geometria = get_object_or_404(Geometria, pk=pk)
    
    # Preparar datos del mapa
    map_data = {
        'geometry': geometria.geojson,
        'bounds': geometria.bounds,
        'name': geometria.nombre,
        'client': geometria.id_cliente.nombre
    }
    
    context = {
        'geometria': geometria,
        'map_data': json.dumps(map_data),
    }
    
    return render(request, 'geometries/geometry_detail.html', context)

@login_required
@admin_required
def geometry_create(request):
    """Crear nueva geometría"""
    if request.method == 'POST':
        form = GeometriaForm(request.POST)
        if form.is_valid():
            geometria = form.save()
            messages.success(request, f'Geometría "{geometria.nombre}" creada exitosamente.')
            return redirect('geometry_detail', pk=geometria.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = GeometriaForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'geometries/geometry_form.html', context)

@login_required
@admin_required
def geometry_edit(request, pk):
    """Editar geometría existente"""
    geometria = get_object_or_404(Geometria, pk=pk)
    
    if request.method == 'POST':
        form = GeometriaForm(request.POST, instance=geometria)
        if form.is_valid():
            geometria = form.save()
            messages.success(request, f'Geometría "{geometria.nombre}" actualizada exitosamente.')
            return redirect('geometry_detail', pk=geometria.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = GeometriaForm(instance=geometria)
    
    # Preparar datos del mapa para edición
    map_data = {
        'geometry': geometria.geojson,
        'bounds': geometria.bounds,
        'name': geometria.nombre,
        'editable': True
    }
    
    context = {
        'form': form,
        'geometria': geometria,
        'action': 'edit',
        'map_data': json.dumps(map_data),
    }
    
    return render(request, 'geometries/geometry_form.html', context)

@login_required
@admin_required
def geometry_delete(request, pk):
    """Eliminar geometría"""
    geometria = get_object_or_404(Geometria, pk=pk)
    
    if request.method == 'POST':
        geometria_nombre = geometria.nombre
        cliente_nombre = geometria.id_cliente.nombre
        geometria.delete()
        messages.success(request, f'Geometría "{geometria_nombre}" del cliente "{cliente_nombre}" eliminada exitosamente.')
        return redirect('geometry_list')
    
    context = {
        'geometria': geometria,
    }
    
    return render(request, 'geometries/geometry_confirm_delete.html', context)

@login_required
@admin_required
def geometry_toggle_monitoring(request, pk):
    """Activar/desactivar monitoreo de geometría"""
    geometria = get_object_or_404(Geometria, pk=pk)
    
    geometria.monitoreo_activo = not geometria.monitoreo_activo
    geometria.save()
    
    status = "activado" if geometria.monitoreo_activo else "desactivado"
    messages.success(request, f'Monitoreo {status} para la geometría "{geometria.nombre}".')
    
    return redirect('geometry_detail', pk=geometria.pk)

@login_required
@admin_required
@require_http_methods(["POST"])
def geometry_validate_geojson(request):
    """Validar GeoJSON via AJAX"""
    try:
        geojson_data = json.loads(request.body)
        geojson = geojson_data.get('geojson')
        
        if not geojson:
            return JsonResponse({
                'valid': False, 
                'error': 'No GeoJSON data provided'
            })
        
        # Validación básica de estructura GeoJSON
        if not isinstance(geojson, dict):
            return JsonResponse({
                'valid': False, 
                'error': 'GeoJSON must be a valid JSON object'
            })
        
        if 'type' not in geojson:
            return JsonResponse({
                'valid': False, 
                'error': 'GeoJSON must have a "type" field'
            })
        
        valid_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 
                      'MultiLineString', 'MultiPolygon', 'GeometryCollection']
        
        if geojson['type'] not in valid_types:
            return JsonResponse({
                'valid': False, 
                'error': f'Invalid geometry type. Must be one of: {", ".join(valid_types)}'
            })
        
        if 'coordinates' not in geojson and geojson['type'] != 'GeometryCollection':
            return JsonResponse({
                'valid': False, 
                'error': 'GeoJSON must have "coordinates" field'
            })
        
        return JsonResponse({
            'valid': True, 
            'message': 'Valid GeoJSON',
            'geometry_type': geojson['type']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'valid': False, 
            'error': 'Invalid JSON format'
        })
    except Exception as e:
        return JsonResponse({
            'valid': False, 
            'error': f'Validation error: {str(e)}'
        })

@login_required
@admin_required
def geometry_map_view(request):
    """Vista del mapa con todas las geometrías"""
    geometrias = Geometria.objects.select_related('id_cliente').filter(
        monitoreo_activo=True
    ).order_by('-creado_en')
    
    # Preparar datos para el mapa
    geometries_data = []
    for geom in geometrias:
        if geom.geojson:
            geometries_data.append({
                'id': geom.id_geometria,
                'name': geom.nombre,
                'client': geom.id_cliente.nombre,
                'geometry': geom.geojson,
                'monitoring': geom.monitoreo_activo,
                'created': geom.creado_en.isoformat()
            })
    
    context = {
        'geometries_data': json.dumps(geometries_data),
        'total_geometrias': len(geometries_data),
    }
    
    return render(request, 'geometries/geometry_map_view.html', context)
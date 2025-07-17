from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Cliente
from .forms import ClienteForm

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
def client_list(request):
    """Lista de clientes con búsqueda y paginación"""
    query = request.GET.get('q', '')
    sector_filter = request.GET.get('sector', '')
    pais_filter = request.GET.get('pais', '')
    activo_filter = request.GET.get('activo', '')
    
    clientes = Cliente.objects.all().order_by('-creado_en')
    
    # Aplicar filtros de búsqueda
    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query) |
            Q(contacto_principal__icontains=query) |
            Q(correo_principal__icontains=query) |
            Q(ejecutivo_lockton__icontains=query)
        )
    
    if sector_filter:
        clientes = clientes.filter(sector__icontains=sector_filter)
    
    if pais_filter:
        clientes = clientes.filter(pais__icontains=pais_filter)
        
    if activo_filter:
        if activo_filter == 'true':
            clientes = clientes.filter(activo=True)
        elif activo_filter == 'false':
            clientes = clientes.filter(activo=False)
    
    # Obtener listas para filtros
    sectores = Cliente.objects.values_list('sector', flat=True).distinct().order_by('sector')
    paises = Cliente.objects.values_list('pais', flat=True).distinct().order_by('pais')
    
    # Paginación
    paginator = Paginator(clientes, 10)  # 10 clientes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_clientes = Cliente.objects.count()
    clientes_activos = Cliente.objects.filter(activo=True).count()
    clientes_inactivos = Cliente.objects.filter(activo=False).count()
    
    context = {
        'clientes': page_obj,
        'query': query,
        'sector_filter': sector_filter,
        'pais_filter': pais_filter,
        'activo_filter': activo_filter,
        'sectores': sectores,
        'paises': paises,
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'clientes_inactivos': clientes_inactivos,
    }
    
    return render(request, 'clients/client_list.html', context)

@login_required
@admin_required
def client_detail(request, pk):
    """Detalle de un cliente específico"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    context = {
        'cliente': cliente,
    }
    
    return render(request, 'clients/client_detail.html', context)

@login_required
@admin_required
def client_create(request):
    """Crear nuevo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nombre}" creado exitosamente.')
            return redirect('client_detail', pk=cliente.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ClienteForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'clients/client_form.html', context)

@login_required
@admin_required
def client_edit(request, pk):
    """Editar cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nombre}" actualizado exitosamente.')
            return redirect('client_detail', pk=cliente.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ClienteForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'action': 'edit'
    }
    
    return render(request, 'clients/client_form.html', context)

@login_required
@admin_required
def client_delete(request, pk):
    """Eliminar cliente (soft delete - marcar como inactivo)"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Soft delete - marcamos como inactivo en lugar de eliminar
        cliente.activo = False
        cliente.save()
        messages.success(request, f'Cliente "{cliente.nombre}" desactivado exitosamente.')
        return redirect('client_list')
    
    context = {
        'cliente': cliente,
    }
    
    return render(request, 'clients/client_confirm_delete.html', context)

@login_required
@admin_required
def client_activate(request, pk):
    """Reactivar cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    cliente.activo = True
    cliente.save()
    messages.success(request, f'Cliente "{cliente.nombre}" reactivado exitosamente.')
    
    return redirect('client_detail', pk=cliente.pk)
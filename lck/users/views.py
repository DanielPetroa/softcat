# En users/views.py - Actualizar la función dashboard

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import User
from .forms import UserCreationForm, UserEditForm
from clients.models import Cliente  # Importar el modelo Cliente
from geometries.models import Geometria  # Importar el modelo Geometria

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    """Dashboard principal con estadísticas"""
    context = {
        'user': request.user,
    }
    
    # Estadísticas para admins
    if request.user.role == 'admin':
        context.update({
            'total_users': User.objects.count(),
            'total_clientes': Cliente.objects.count(),
            'clientes_activos': Cliente.objects.filter(activo=True).count(),
            'clientes_inactivos': Cliente.objects.filter(activo=False).count(),
            'total_geometrias': Geometria.objects.count(),
            'geometrias_activas': Geometria.objects.filter(monitoreo_activo=True).count(),
            'geometrias_inactivas': Geometria.objects.filter(monitoreo_activo=False).count(),
        })
    elif request.user.role in ['cliente', 'client'] and request.user.cliente_relacionado:
        # Estadísticas para clientes (solo sus geometrías)
        client_geometrias = Geometria.objects.filter(id_cliente=request.user.cliente_relacionado)
        context.update({
            'total_geometrias': client_geometrias.count(),
            'geometrias_activas': client_geometrias.filter(monitoreo_activo=True).count(),
            'geometrias_inactivas': client_geometrias.filter(monitoreo_activo=False).count(),
        })
    
    return render(request, 'users/dashboard.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})

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
def user_list(request):
    """Lista de usuarios - solo para admin"""
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
    }
    return render(request, 'users/user_list.html', context)

@login_required
@admin_required
def user_create(request):
    """Crear nuevo usuario - solo para admin"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario "{user.username}" creado exitosamente.')
            return redirect('user_list')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'users/user_create.html', context)

@login_required
@admin_required
def user_edit(request, user_id):
    """Editar usuario - solo para admin"""
    edit_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=edit_user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario "{user.username}" actualizado exitosamente.')
            return redirect('user_list')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserEditForm(instance=edit_user)
    
    context = {
        'form': form,
        'edit_user': edit_user,
    }
    return render(request, 'users/user_edit.html', context)

#debug

# Agrega esta función a users/views.py

@login_required
def debug_permissions(request):
    """Vista para debuggear permisos de geometrías"""
    
    debug_info = {
        'user_authenticated': request.user.is_authenticated,
        'username': request.user.username,
        'user_role_raw': repr(request.user.role),  # repr muestra comillas y espacios
        'user_role_length': len(request.user.role) if request.user.role else 0,
        'role_equals_cliente': request.user.role == 'cliente',
        'role_equals_admin': request.user.role == 'admin',
        'role_in_list': request.user.role in ['admin', 'cliente'],
        'cliente_relacionado': request.user.cliente_relacionado,
        'cliente_relacionado_id': request.user.cliente_relacionado.id_cliente if request.user.cliente_relacionado else None,
    }
    
    # Test del decorador manualmente
    if not request.user.is_authenticated:
        debug_info['decorator_result'] = 'FAIL: Not authenticated'
    elif request.user.role not in ['admin', 'cliente']:
        debug_info['decorator_result'] = f'FAIL: Role "{request.user.role}" not in [admin, cliente]'
    else:
        debug_info['decorator_result'] = 'PASS: Should have access'
    
    # Test de geometrías
    try:
        from geometries.views import get_user_geometries
        user_geometrias = get_user_geometries(request.user)
        debug_info['geometrias_count'] = user_geometrias.count()
        debug_info['geometrias_access'] = 'SUCCESS'
    except Exception as e:
        debug_info['geometrias_count'] = 'ERROR'
        debug_info['geometrias_access'] = str(e)
    
    return render(request, 'debug_permissions.html', {'debug_info': debug_info})
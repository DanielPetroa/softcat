from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import UserCreateForm, UserEditForm
from .models import User

def login_view(request):
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        username = request.POST['username']
        password = request.POST['password']
        remember_me = request.POST.get('remember_me')  # Obtener el checkbox
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            
            # Configurar la duración de la sesión basada en "Remember me"
            if not remember_me:
                # Si no marcó "Remember me", la sesión expira al cerrar el navegador
                request.session.set_expiry(0)
            else:
                # Si marcó "Remember me", la sesión dura 30 días (configurable)
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 días en segundos
            
            return redirect('dashboard')
        messages.error(request, 'Credenciales inválidas')
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')

@login_required
def user_list(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    users = User.objects.all()
    return render(request, 'users/user_list.html', {'users': users})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully')
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def user_create(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'users/user_create.html', {'form': form})

@login_required
def user_edit(request, user_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    edit_user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=edit_user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully')
            return redirect('user_list')
    else:
        form = UserEditForm(instance=edit_user)
    
    return render(request, 'users/user_edit.html', {'form': form, 'edit_user': edit_user})
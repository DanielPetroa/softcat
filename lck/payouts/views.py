from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import Http404
from .models import PayoutOption
from .forms import PayoutForm, PayoutSearchForm
from geometries.models import Geometria

def admin_required(view_func):
    """Decorator to ensure only admin users can access payout management"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            raise Http404("Page not found")
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def payout_list(request):
    """List all payout options with search and filtering"""
    
    # Initialize search form
    search_form = PayoutSearchForm(request.GET)
    payouts = PayoutOption.objects.select_related(
        'id_geometria', 
        'id_geometria__id_cliente'
    ).all()

    # Apply search filters
    if search_form.is_valid():
        q = search_form.cleaned_data.get('q')
        geometria = search_form.cleaned_data.get('geometria')
        trigger_type = search_form.cleaned_data.get('trigger_type')
        payout_method = search_form.cleaned_data.get('payout_method')
        activo = search_form.cleaned_data.get('activo')

        if q:
            payouts = payouts.filter(
                Q(id_geometria__nombre__icontains=q) |
                Q(id_geometria__id_cliente__nombre__icontains=q) |
                Q(trigger_type__icontains=q) |
                Q(int_var__icontains=q) |
                Q(payout_method_by_geom__icontains=q)
            )

        if geometria:
            payouts = payouts.filter(id_geometria=geometria)

        if trigger_type:
            payouts = payouts.filter(trigger_type=trigger_type)

        if payout_method:
            payouts = payouts.filter(payout_method_by_geom=payout_method)

        if activo:
            payouts = payouts.filter(activo=activo == 'true')

    # Calculate statistics
    total_payouts = PayoutOption.objects.count()
    active_payouts = PayoutOption.objects.filter(activo=True).count()
    inactive_payouts = total_payouts - active_payouts
    
    # Get unique trigger types and payout methods for statistics
    trigger_types = PayoutOption.objects.values_list('trigger_type', flat=True).distinct()
    payout_methods = PayoutOption.objects.values_list('payout_method_by_geom', flat=True).distinct()

    # Pagination
    paginator = Paginator(payouts, 10)  # 10 payouts per page
    page = request.GET.get('page')
    payouts = paginator.get_page(page)

    context = {
        'payouts': payouts,
        'search_form': search_form,
        'total_payouts': total_payouts,
        'active_payouts': active_payouts,
        'inactive_payouts': inactive_payouts,
        'trigger_types': trigger_types,
        'payout_methods': payout_methods,
        'query': request.GET.get('q', ''),
        'geometria_filter': request.GET.get('geometria', ''),
        'trigger_filter': request.GET.get('trigger_type', ''),
        'method_filter': request.GET.get('payout_method', ''),
        'activo_filter': request.GET.get('activo', ''),
    }
    
    return render(request, 'payouts/payout_list.html', context)

@admin_required
def payout_detail(request, pk):
    """Display detailed view of a payout option"""
    payout = get_object_or_404(
        PayoutOption.objects.select_related(
            'id_geometria',
            'id_geometria__id_cliente'
        ), 
        id_payout_option=pk
    )
    
    context = {
        'payout': payout,
    }
    
    return render(request, 'payouts/payout_detail.html', context)

@admin_required
def payout_create(request):
    """Create a new payout option"""
    if request.method == 'POST':
        form = PayoutForm(request.POST)
        if form.is_valid():
            payout = form.save()
            messages.success(
                request, 
                f'Payout option created successfully for {payout.id_geometria.nombre}!'
            )
            return redirect('payout_detail', pk=payout.id_payout_option)
    else:
        form = PayoutForm()
        
        # Pre-select geometry if provided via URL
        geometry_id = request.GET.get('geometry')
        if geometry_id:
            try:
                geometry = Geometria.objects.get(id_geometria=geometry_id)
                form.initial['id_geometria'] = geometry
            except Geometria.DoesNotExist:
                pass

    context = {
        'form': form,
        'action': 'create',
    }
    
    return render(request, 'payouts/payout_form.html', context)

@admin_required
def payout_edit(request, pk):
    """Edit an existing payout option"""
    payout = get_object_or_404(PayoutOption, id_payout_option=pk)
    
    if request.method == 'POST':
        form = PayoutForm(request.POST, instance=payout)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payout option updated successfully!')
            return redirect('payout_detail', pk=payout.id_payout_option)
    else:
        form = PayoutForm(instance=payout)

    context = {
        'form': form,
        'payout': payout,
        'action': 'edit',
    }
    
    return render(request, 'payouts/payout_form.html', context)

@admin_required
def payout_delete(request, pk):
    """Delete (deactivate) a payout option"""
    payout = get_object_or_404(PayoutOption, id_payout_option=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Instead of deleting, deactivate the payout
        payout.activo = False
        payout.save()
        
        messages.warning(
            request, 
            f'Payout option for {payout.id_geometria.nombre} has been deactivated.'
        )
        return redirect('payout_list')

    context = {
        'payout': payout,
    }
    
    return render(request, 'payouts/payout_confirm_delete.html', context)

@admin_required
def payout_activate(request, pk):
    """Reactivate a payout option"""
    payout = get_object_or_404(PayoutOption, id_payout_option=pk)
    
    if request.method == 'POST':
        payout.activo = True
        payout.save()
        
        messages.success(
            request, 
            f'Payout option for {payout.id_geometria.nombre} has been reactivated.'
        )
        return redirect('payout_detail', pk=payout.id_payout_option)
    
    return redirect('payout_detail', pk=payout.id_payout_option)

@admin_required
def payout_by_geometry(request, geometry_id):
    """List all payout options for a specific geometry"""
    geometry = get_object_or_404(Geometria, id_geometria=geometry_id)
    payouts = PayoutOption.objects.filter(id_geometria=geometry).order_by('-creado_en')
    
    # Calculate statistics for this geometry
    total_payouts = payouts.count()
    active_payouts = payouts.filter(activo=True).count()
    
    context = {
        'geometry': geometry,
        'payouts': payouts,
        'total_payouts': total_payouts,
        'active_payouts': active_payouts,
    }
    
    return render(request, 'payouts/payout_by_geometry.html', context)

@admin_required
def payout_duplicate(request, pk):
    """Create a duplicate of an existing payout option"""
    original_payout = get_object_or_404(PayoutOption, id_payout_option=pk)
    
    if request.method == 'POST':
        form = PayoutForm(request.POST)
        if form.is_valid():
            new_payout = form.save()
            messages.success(
                request, 
                f'Payout option duplicated successfully! Original: {original_payout.id_payout_option}, New: {new_payout.id_payout_option}'
            )
            return redirect('payout_detail', pk=new_payout.id_payout_option)
    else:
        # Pre-populate form with original payout data
        form = PayoutForm(instance=original_payout)
        form.instance.pk = None  # Clear the primary key to create new instance

    context = {
        'form': form,
        'original_payout': original_payout,
        'action': 'duplicate',
    }
    
    return render(request, 'payouts/payout_form.html', context)
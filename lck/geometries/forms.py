from django import forms
from django.core.exceptions import ValidationError
from .models import Geometria
from clients.models import Cliente
import json

class GeoJSONWidget(forms.Textarea):
    """Widget personalizado para editar GeoJSON"""
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control geojson-editor',
            'rows': 8,
            'placeholder': 'Paste or edit GeoJSON here...',
            'data-language': 'json'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class GeometriaForm(forms.ModelForm):
    """Formulario para crear y editar geometrías"""
    
    # Campo personalizado para GeoJSON
    geojson_text = forms.CharField(
        widget=GeoJSONWidget(),
        label="GeoJSON Geometry",
        help_text="Paste a valid GeoJSON geometry or use the map editor below.",
        required=True
    )
    
    class Meta:
        model = Geometria
        fields = ['nombre', 'id_cliente', 'geojson', 'monitoreo_activo']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter geometry name'
            }),
            'id_cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'geojson': forms.HiddenInput(),  # Campo oculto, se maneja via geojson_text
            'monitoreo_activo': forms.CheckboxInput(attrs={
                'class': 'custom-control-input'
            }),
        }
        
        labels = {
            'nombre': 'Geometry Name',
            'id_cliente': 'Client',
            'monitoreo_activo': 'Active Monitoring',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para clientes activos
        self.fields['id_cliente'].queryset = Cliente.objects.filter(activo=True).order_by('nombre')
        self.fields['id_cliente'].empty_label = "Select a client"
        
        # Marcar campos requeridos
        self.fields['nombre'].required = True
        self.fields['id_cliente'].required = True
        
        # Si estamos editando, prellenar el campo geojson_text
        if self.instance and self.instance.pk and self.instance.geojson:
            self.fields['geojson_text'].initial = json.dumps(self.instance.geojson, indent=2)
        else:
            # Ejemplo de GeoJSON para nuevas geometrías
            example_geojson = {
                "type": "Point",
                "coordinates": [-74.0059, 40.7128]  # NYC coordinates as example
            }
            self.fields['geojson_text'].initial = json.dumps(example_geojson, indent=2)

    def clean_geojson_text(self):
        """Validar y convertir el texto GeoJSON"""
        geojson_text = self.cleaned_data.get('geojson_text')
        
        if not geojson_text:
            raise ValidationError("GeoJSON is required.")
        
        try:
            # Intentar parsear el JSON
            geojson_data = json.loads(geojson_text)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")
        
        # Validar estructura GeoJSON
        if not isinstance(geojson_data, dict):
            raise ValidationError("GeoJSON must be a JSON object.")
        
        if 'type' not in geojson_data:
            raise ValidationError("GeoJSON must have a 'type' field.")
        
        valid_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 
                      'MultiLineString', 'MultiPolygon', 'GeometryCollection']
        
        if geojson_data['type'] not in valid_types:
            raise ValidationError(f"Invalid geometry type '{geojson_data['type']}'. "
                                f"Must be one of: {', '.join(valid_types)}")
        
        # Validar que tenga coordenadas (excepto GeometryCollection)
        if geojson_data['type'] != 'GeometryCollection' and 'coordinates' not in geojson_data:
            raise ValidationError("GeoJSON must have 'coordinates' field.")
        
        # Validaciones específicas por tipo de geometría
        if geojson_data['type'] == 'Point':
            coords = geojson_data.get('coordinates', [])
            if not isinstance(coords, list) or len(coords) < 2:
                raise ValidationError("Point coordinates must be [longitude, latitude].")
            
            # Validar rangos de coordenadas
            lng, lat = coords[0], coords[1]
            if not (-180 <= lng <= 180):
                raise ValidationError(f"Longitude {lng} is out of valid range [-180, 180].")
            if not (-90 <= lat <= 90):
                raise ValidationError(f"Latitude {lat} is out of valid range [-90, 90].")
        
        elif geojson_data['type'] == 'Polygon':
            coords = geojson_data.get('coordinates', [])
            if not isinstance(coords, list) or len(coords) == 0:
                raise ValidationError("Polygon must have at least one linear ring.")
            
            for ring in coords:
                if not isinstance(ring, list) or len(ring) < 4:
                    raise ValidationError("Polygon linear ring must have at least 4 coordinates.")
                
                # Verificar que el primer y último punto sean iguales
                if ring[0] != ring[-1]:
                    raise ValidationError("Polygon linear ring must be closed (first and last coordinates must be the same).")
        
        return geojson_data

    def clean_nombre(self):
        """Validar nombre único por cliente"""
        nombre = self.cleaned_data.get('nombre')
        id_cliente = self.cleaned_data.get('id_cliente')
        
        if nombre and id_cliente:
            # Verificar que no exista otra geometría con el mismo nombre para el mismo cliente
            existing = Geometria.objects.filter(nombre=nombre, id_cliente=id_cliente)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f"A geometry named '{nombre}' already exists for this client.")
        
        return nombre

    def save(self, commit=True):
        """Guardar el formulario procesando el GeoJSON"""
        instance = super().save(commit=False)
        
        # Asignar el GeoJSON procesado desde geojson_text
        if 'geojson_text' in self.cleaned_data:
            instance.geojson = self.cleaned_data['geojson_text']
        
        if commit:
            instance.save()
        return instance

class GeometriaSearchForm(forms.Form):
    """Formulario para búsqueda y filtros de geometrías"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or client...',
        }),
        label='Search'
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True).order_by('nombre'),
        required=False,
        empty_label="All Clients",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Client'
    )
    
    tipo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Types'),
            ('Point', 'Point'),
            ('LineString', 'Line String'),
            ('Polygon', 'Polygon'),
            ('MultiPoint', 'Multi Point'),
            ('MultiLineString', 'Multi Line String'),
            ('MultiPolygon', 'Multi Polygon'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Geometry Type'
    )
    
    monitoreo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('true', 'Active Monitoring'),
            ('false', 'Inactive Monitoring'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Monitoring Status'
    )

class GeometriaQuickCreateForm(forms.ModelForm):
    """Formulario simplificado para crear geometrías rápidamente"""
    
    class Meta:
        model = Geometria
        fields = ['nombre', 'id_cliente']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quick geometry name'
            }),
            'id_cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_cliente'].queryset = Cliente.objects.filter(activo=True).order_by('nombre')
        self.fields['id_cliente'].empty_label = "Select a client"
    
    def save(self, commit=True):
        """Guardar con una geometría por defecto"""
        instance = super().save(commit=False)
        
        # Asignar una geometría por defecto (punto en coordenadas 0,0)
        if not instance.geojson:
            instance.geojson = {
                "type": "Point",
                "coordinates": [0, 0]
            }
        
        if commit:
            instance.save()
        return instance
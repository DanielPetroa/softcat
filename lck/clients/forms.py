from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    """Formulario para crear y editar clientes"""
    
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'tipo', 'sector', 'sector_retail', 'pais', 'direccion',
            'contacto_principal', 'correo_principal', 'celular_principal',
            'contacto_alterno', 'correo_alterno', 'celular_alterno',
            'ejecutivo_lockton', 'correo_ejecutivo', 'activo'
        ]
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del cliente'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Seleccionar tipo'),
                ('Empresa', 'Empresa'),
                ('Persona Natural', 'Persona Natural'),
                ('Corporativo', 'Corporativo'),
                ('PYME', 'PYME'),
                ('Multinacional', 'Multinacional'),
            ]),
            'sector': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Seleccionar sector'),
                ('Agricultura', 'Agricultura'),
                ('Construcción', 'Construcción'),
                ('Educación', 'Educación'),
                ('Energía', 'Energía'),
                ('Financiero', 'Financiero'),
                ('Gobierno', 'Gobierno'),
                ('Salud', 'Salud'),
                ('Manufactura', 'Manufactura'),
                ('Minería', 'Minería'),
                ('Retail', 'Retail'),
                ('Servicios', 'Servicios'),
                ('Tecnología', 'Tecnología'),
                ('Telecomunicaciones', 'Telecomunicaciones'),
                ('Transporte', 'Transporte'),
                ('Turismo', 'Turismo'),
                ('Otro', 'Otro'),
            ]),
            'sector_retail': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Especificar si es sector retail'
            }),
            'pais': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Seleccionar país'),
                ('Colombia', 'Colombia'),
                ('México', 'México'),
                ('Perú', 'Perú'),
                ('Chile', 'Chile'),
                ('Argentina', 'Argentina'),
                ('Brasil', 'Brasil'),
                ('Ecuador', 'Ecuador'),
                ('Venezuela', 'Venezuela'),
                ('Estados Unidos', 'Estados Unidos'),
                ('Canadá', 'Canadá'),
                ('España', 'España'),
                ('Otro', 'Otro'),
            ]),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa del cliente'
            }),
            'contacto_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del contacto principal'
            }),
            'correo_principal': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.com'
            }),
            'celular_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 300 123 4567'
            }),
            'contacto_alterno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del contacto alterno (opcional)'
            }),
            'correo_alterno': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo.alterno@empresa.com'
            }),
            'celular_alterno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 300 123 4567'
            }),
            'ejecutivo_lockton': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del ejecutivo de Lockton'
            }),
            'correo_ejecutivo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejecutivo@lockton.com'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'custom-control-input'
            }),
        }
        
        labels = {
            'nombre': 'Nombre del Cliente',
            'tipo': 'Tipo de Cliente',
            'sector': 'Sector Económico',
            'sector_retail': 'Sector Retail Específico',
            'pais': 'País',
            'direccion': 'Dirección',
            'contacto_principal': 'Contacto Principal',
            'correo_principal': 'Correo Principal',
            'celular_principal': 'Celular Principal',
            'contacto_alterno': 'Contacto Alterno',
            'correo_alterno': 'Correo Alterno',
            'celular_alterno': 'Celular Alterno',
            'ejecutivo_lockton': 'Ejecutivo Lockton',
            'correo_ejecutivo': 'Correo Ejecutivo',
            'activo': 'Cliente Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marcar campos requeridos con *
        required_fields = ['nombre', 'tipo', 'sector', 'pais', 'direccion', 
                          'contacto_principal', 'correo_principal', 'celular_principal',
                          'ejecutivo_lockton', 'correo_ejecutivo']
        
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].widget.attrs['required'] = 'required'
        
        # Campos opcionales
        optional_fields = ['sector_retail', 'contacto_alterno', 'correo_alterno', 'celular_alterno']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def clean_correo_principal(self):
        """Validación personalizada para correo principal"""
        correo = self.cleaned_data.get('correo_principal')
        if correo:
            # Verificar que no exista otro cliente con el mismo correo principal
            existing = Cliente.objects.filter(correo_principal=correo)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("Ya existe un cliente con este correo principal.")
        return correo

    def clean_celular_principal(self):
        """Validación personalizada para celular principal"""
        celular = self.cleaned_data.get('celular_principal')
        if celular:
            # Limpiar formato (eliminar espacios y caracteres especiales)
            celular_limpio = ''.join(filter(str.isdigit, celular.replace('+', '')))
            if len(celular_limpio) < 7:
                raise forms.ValidationError("El número de celular debe tener al menos 7 dígitos.")
        return celular

    def clean(self):
        """Validación general del formulario"""
        cleaned_data = super().clean()
        sector = cleaned_data.get('sector')
        sector_retail = cleaned_data.get('sector_retail')
        
        # Si el sector es Retail, el sector_retail debe estar especificado
        if sector == 'Retail' and not sector_retail:
            self.add_error('sector_retail', 'Debe especificar el tipo de retail cuando el sector es Retail.')
        
        return cleaned_data
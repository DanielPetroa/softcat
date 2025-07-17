from django import forms
from django.core.exceptions import ValidationError
from .models import PayoutOption
from geometries.models import Geometria

class PayoutForm(forms.ModelForm):
    class Meta:
        model = PayoutOption
        fields = [
            'id_geometria', 'trigger_type', 'int_var', 'int_val1', 'int_val2',
            'filter_var', 'filter_value', 'filter_condition',
            'payout_percent_limit1', 'payout_percent_limit2', 'payout_method_by_geom',
            'activo'
        ]
        widgets = {
            'id_geometria': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'trigger_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'int_var': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., wind_speed, precipitation, magnitude',
                'required': True
            }),
            'int_val1': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'required': True
            }),
            'int_val2': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00 (optional)'
            }),
            'filter_var': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., location, depth, duration'
            }),
            'filter_value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Filter value'
            }),
            'filter_condition': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payout_percent_limit1': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00',
                'required': True
            }),
            'payout_percent_limit2': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00 (optional)'
            }),
            'payout_method_by_geom': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'custom-control-input',
                'id': 'activo'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter geometries to only show active ones
        self.fields['id_geometria'].queryset = Geometria.objects.filter(
            id_cliente__activo=True
        ).select_related('id_cliente')
        
        # Customize geometry display
        self.fields['id_geometria'].empty_label = "Select a geometry..."
        
        # Add help texts
        self.fields['trigger_type'].help_text = "Select the type of trigger mechanism"
        self.fields['int_var'].help_text = "Variable to monitor for triggering payout"
        self.fields['int_val1'].help_text = "Primary threshold value"
        self.fields['int_val2'].help_text = "Secondary threshold (for tiered payouts)"
        self.fields['payout_percent_limit1'].help_text = "Percentage of limit to pay out (0-100%)"
        self.fields['payout_percent_limit2'].help_text = "Additional percentage for second tier"
        self.fields['payout_method_by_geom'].help_text = "How payout is calculated based on geometry"

    def clean(self):
        cleaned_data = super().clean()
        
        # Get form values
        payout1 = cleaned_data.get('payout_percent_limit1')
        payout2 = cleaned_data.get('payout_percent_limit2')
        int_val1 = cleaned_data.get('int_val1')
        int_val2 = cleaned_data.get('int_val2')
        trigger_type = cleaned_data.get('trigger_type')
        filter_var = cleaned_data.get('filter_var')
        filter_value = cleaned_data.get('filter_value')
        filter_condition = cleaned_data.get('filter_condition')

        # Validate payout percentages
        if payout1 is not None:
            if payout1 < 0 or payout1 > 100:
                raise ValidationError({
                    'payout_percent_limit1': 'Percentage must be between 0 and 100'
                })

        if payout2 is not None:
            if payout2 < 0 or payout2 > 100:
                raise ValidationError({
                    'payout_percent_limit2': 'Percentage must be between 0 and 100'
                })

        # Validate total payout doesn't exceed 100%
        if payout1 and payout2:
            total = payout1 + payout2
            if total > 100:
                raise ValidationError({
                    'payout_percent_limit2': f'Total payout percentage ({total}%) cannot exceed 100%'
                })

        # Validate threshold values relationship
        if int_val1 is not None and int_val2 is not None:
            if trigger_type in ['threshold', 'parametric']:
                if int_val2 <= int_val1:
                    raise ValidationError({
                        'int_val2': 'Second threshold must be greater than first threshold'
                    })

        # Validate filter consistency
        filter_fields = [filter_var, filter_value, filter_condition]
        if any(filter_fields) and not all(filter_fields):
            missing_fields = []
            if not filter_var:
                missing_fields.append('filter_var')
            if not filter_value:
                missing_fields.append('filter_value')
            if not filter_condition:
                missing_fields.append('filter_condition')
            
            raise ValidationError({
                'filter_var': 'All filter fields must be provided when using filters'
            })

        return cleaned_data

    def clean_int_val1(self):
        value = self.cleaned_data.get('int_val1')
        if value is not None and value < 0:
            raise ValidationError('Threshold value cannot be negative')
        return value

    def clean_int_val2(self):
        value = self.cleaned_data.get('int_val2')
        if value is not None and value < 0:
            raise ValidationError('Threshold value cannot be negative')
        return value


class PayoutSearchForm(forms.Form):
    """Form for searching and filtering payout options"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by geometry, client, trigger...'
        })
    )
    
    geometria = forms.ModelChoiceField(
        queryset=Geometria.objects.all(),
        required=False,
        empty_label="All Geometries",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    trigger_type = forms.ChoiceField(
        choices=[('', 'All Trigger Types')] + PayoutOption.TRIGGER_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payout_method = forms.ChoiceField(
        choices=[('', 'All Methods')] + PayoutOption.PAYOUT_METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('true', 'Active'),
            ('false', 'Inactive')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show geometries from active clients
        self.fields['geometria'].queryset = Geometria.objects.filter(
            id_cliente__activo=True
        ).select_related('id_cliente').order_by('id_cliente__nombre', 'nombre')
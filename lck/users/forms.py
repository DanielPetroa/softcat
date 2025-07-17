from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from clients.models import Cliente

class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    cliente_relacionado = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        required=False,
        help_text="Select the client for this user (required for client role)"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'cliente_relacionado', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'cliente_relacionado', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Filtrar solo clientes activos
        self.fields['cliente_relacionado'].queryset = Cliente.objects.filter(activo=True)
        self.fields['cliente_relacionado'].required = False
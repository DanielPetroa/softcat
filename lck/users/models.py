from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('client', 'Cliente'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    cliente_relacionado = models.ForeignKey(
        'clients.Cliente', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
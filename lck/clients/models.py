from django.db import models

class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)  # PK personalizada
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    sector_retail = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=100)
    direccion = models.TextField()
    contacto_principal = models.CharField(max_length=200)
    correo_principal = models.EmailField()
    celular_principal = models.CharField(max_length=20)
    contacto_alterno = models.CharField(max_length=200, blank=True)
    correo_alterno = models.EmailField(blank=True)
    celular_alterno = models.CharField(max_length=20, blank=True)
    ejecutivo_lockton = models.CharField(max_length=200)
    correo_ejecutivo = models.EmailField()
    creado_en = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_cliente}-{self.nombre}"  # Formato: 123456-Lockton

    class Meta:
        verbose_name_plural = "Clientes"
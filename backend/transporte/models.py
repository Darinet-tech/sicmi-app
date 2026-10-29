from django.conf import settings
from django.db import models

from accounts.models import UnidadOrganizativa


class Vehiculo(models.Model):
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='vehiculos')
    chapa = models.CharField(max_length=20)
    tipo = models.CharField(max_length=60, blank=True, help_text='Ej.: camioneta, camión, moto')
    descripcion = models.CharField(max_length=150, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['uo', 'chapa']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'chapa'], name='vehiculo_unico_por_uo')
        ]

    def __str__(self):
        return f'{self.chapa} ({self.tipo})' if self.tipo else self.chapa


class EstadoVehiculo(models.Model):
    """Estado de un vehículo en una fecha (historial diario)."""

    class Estado(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        TALLER = 'TALLER', 'Paralizado en taller'
        COMBUSTIBLE = 'COMBUSTIBLE', 'Paralizado por combustible'
        OTRAS = 'OTRAS', 'Paralizado por otras causas'

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='estados')
    fecha = models.DateField()
    estado = models.CharField(max_length=15, choices=Estado.choices)
    motivo = models.CharField(max_length=200, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado de vehículo'
        verbose_name_plural = 'Estados de vehículos'
        ordering = ['-fecha']
        constraints = [
            models.UniqueConstraint(fields=['vehiculo', 'fecha'], name='estado_vehiculo_unico_por_dia')
        ]

    def __str__(self):
        return f'{self.vehiculo} {self.fecha}: {self.get_estado_display()}'
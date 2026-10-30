from django.conf import settings
from django.db import models

from accounts.models import UnidadOrganizativa
from catalogos.models import Inmueble, CentroCosto, AreaSolicitante, Local, GrupoGenerico


class Solicitud(models.Model):
    """REG.1 - Solicitud de Servicio de Mantenimiento (Anexo 1)."""

    class Estado(models.TextChoices):
        ENVIADA = 'ENVIADA', 'Enviada'
        EN_REVISION = 'EN_REVISION', 'En revisión'
        DEVUELTA = 'DEVUELTA', 'Devuelta al cliente'
        EN_INSPECCION = 'EN_INSPECCION', 'En inspección'
        EN_PROGRAMACION = 'EN_PROGRAMACION', 'En programación'
        ORDEN_GENERADA = 'ORDEN_GENERADA', 'Orden generada'
        CERRADA = 'CERRADA', 'Cerrada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='solicitudes')
    inmueble = models.ForeignKey(Inmueble, on_delete=models.PROTECT, related_name='solicitudes')
    centro_costo = models.ForeignKey(CentroCosto, on_delete=models.PROTECT, related_name='solicitudes')
    area_solicitante = models.ForeignKey(AreaSolicitante, on_delete=models.PROTECT, related_name='solicitudes')
    local = models.ForeignKey(
        Local, on_delete=models.PROTECT, related_name='solicitudes',
        verbose_name='Local donde ocurre la incidencia',
    )
    # Afectación: un grupo genérico, o texto libre si no está en la lista
    afectacion = models.ForeignKey(
        GrupoGenerico, null=True, blank=True, on_delete=models.PROTECT, related_name='solicitudes'
    )
    otra_afectacion = models.CharField(max_length=150, blank=True)
    descripcion = models.TextField('Descripción de las afectaciones')
    foto = models.ImageField(upload_to='solicitudes/', null=True, blank=True)

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='solicitudes_creadas'
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ENVIADA)
    es_urgente = models.BooleanField(default=False)
    motivo_devolucion = models.TextField(blank=True)

    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Solicitudes'
        ordering = ['-creada']

    def __str__(self):
        return f'Solicitud {self.pk} - {self.inmueble} ({self.get_estado_display()})'


class HistorialEstado(models.Model):
    """Registro de cada cambio de estado: quién, cuándo y por qué (auditoría)."""
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=20, blank=True)
    estado_nuevo = models.CharField(max_length=20)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
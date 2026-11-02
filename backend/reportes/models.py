from django.conf import settings
from django.db import models

from accounts.models import UnidadOrganizativa


class Certificacion(models.Model):
    """REG.5 - Certificación mensual de mantenimiento de inmuebles por medios propios en físico (Anexo 10)."""

    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'En elaboración'
        EN_FIRMAS = 'EN_FIRMAS', 'En revisión y firmas'
        APROBADA = 'APROBADA', 'Aprobada'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='certificaciones')
    anio = models.PositiveSmallIntegerField('Año')
    mes = models.PositiveSmallIntegerField('Mes')
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BORRADOR)
    # Foto de los datos calculados al generarla (filas e indicadores)
    datos = models.JSONField(default=dict, blank=True)
    # {"clave de fila": "texto"} escrito por el Especialista
    incidencias = models.JSONField(default=dict, blank=True)
    motivo_devolucion = models.TextField(blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Certificación mensual'
        verbose_name_plural = 'Certificaciones mensuales'
        ordering = ['-anio', '-mes', 'uo']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'anio', 'mes'], name='certificacion_unica_por_mes')
        ]

    def __str__(self):
        return f'Certificación {self.mes:02d}/{self.anio} · {self.uo.acronimo}'


class CertificacionFirma(models.Model):
    certificacion = models.ForeignKey(Certificacion, on_delete=models.CASCADE, related_name='firmas')
    rol = models.CharField(max_length=20)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
        constraints = [
            models.UniqueConstraint(fields=['certificacion', 'rol'], name='una_firma_certificacion_por_rol')
        ]


class HistorialCertificacion(models.Model):
    certificacion = models.ForeignKey(Certificacion, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
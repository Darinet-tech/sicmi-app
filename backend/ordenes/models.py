from django.conf import settings
from django.db import models
from django.db.models import Max, Q

from accounts.models import UnidadOrganizativa
from catalogos.models import Inmueble, CentroCosto, AreaSolicitante, Local
from personal.models import Trabajador, Brigada
from solicitudes.models import Solicitud
from transporte.models import Vehiculo


class Orden(models.Model):
    """REG.3 - Orden de Trabajo para la actividad de mantenimiento de inmuebles (Anexo 6)."""

    class Tipo(models.TextChoices):
        CORRECTIVO = 'MC', 'Correctivo'
        PREVENTIVO = 'MP', 'Preventivo'

    class Estado(models.TextChoices):
        REGISTRADA = 'REGISTRADA', 'Registrada'
        EN_EJECUCION = 'EN_EJECUCION', 'En ejecución'
        ENTREGADA = 'ENTREGADA', 'Entregada al cliente'
        CONFORME = 'CONFORME', 'Conforme (en firmas)'
        CERRADA = 'CERRADA', 'Cerrada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='ordenes')
    anio = models.PositiveSmallIntegerField()
    numero = models.PositiveIntegerField()
    tipo = models.CharField(max_length=2, choices=Tipo.choices, default=Tipo.CORRECTIVO)
    # Vacía en los mantenimientos preventivos (nacen del Plan Anual)
    solicitud = models.OneToOneField(
        Solicitud, null=True, blank=True, on_delete=models.PROTECT, related_name='orden'
    )

    inmueble = models.ForeignKey(Inmueble, on_delete=models.PROTECT, related_name='ordenes')
    centro_costo = models.ForeignKey(CentroCosto, on_delete=models.PROTECT, related_name='ordenes')
    area_solicitante = models.ForeignKey(AreaSolicitante, on_delete=models.PROTECT, related_name='ordenes')
    local = models.ForeignKey(Local, null=True, blank=True, on_delete=models.PROTECT, related_name='ordenes')
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='ordenes_cliente'
    )

    # Copiados de la solicitud al generar la orden
    afectacion = models.CharField(max_length=200, blank=True)
    descripcion_solicitud = models.TextField(blank=True)
    inspeccion_por = models.CharField('Inspección realizada por', max_length=150, blank=True)

    vehiculo = models.ForeignKey(Vehiculo, null=True, blank=True, on_delete=models.PROTECT, related_name='ordenes')
    descripcion_trabajos = models.TextField('Descripción de los trabajos realizados', blank=True)
    incidencias = models.TextField('Incidencias a reportar', blank=True)

    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.REGISTRADA)
    fecha_solicitud = models.DateField()
    fecha_cierre = models.DateField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Orden de trabajo'
        verbose_name_plural = 'Órdenes de trabajo'
        ordering = ['-anio', '-numero']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'anio', 'numero'], name='orden_consecutivo_unico')
        ]

    @property
    def codigo(self):
        """Formato AA-NNN: dos dígitos del año y tres del consecutivo (ej. 26-001)."""
        return f'{self.anio % 100:02d}-{self.numero:03d}'

    @classmethod
    def siguiente_numero(cls, uo, anio):
        ultimo = cls.objects.filter(uo=uo, anio=anio).aggregate(m=Max('numero'))['m'] or 0
        return ultimo + 1

    def __str__(self):
        return f'Orden {self.codigo} ({self.uo.acronimo})'


class BrigadaOrden(models.Model):
    """Brigadas que trabajaron en la orden, con fechas (hasta vacío = vigente)."""
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='brigadas')
    brigada = models.ForeignKey(Brigada, on_delete=models.PROTECT, related_name='+')
    desde = models.DateField()
    hasta = models.DateField(null=True, blank=True)


class ParticipanteOrden(models.Model):
    """Operarios que participaron en la orden. Nunca se borran: se les pone fecha de fin."""
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='participantes')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.PROTECT, related_name='participaciones')
    brigada = models.ForeignKey(Brigada, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    desde = models.DateField()
    hasta = models.DateField(null=True, blank=True)
    motivo = models.CharField(max_length=200, blank=True)
    agregado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        constraints = [
            # Un trabajador no puede estar dos veces vigente en la misma orden
            models.UniqueConstraint(
                fields=['orden', 'trabajador'], condition=Q(hasta__isnull=True),
                name='participante_vigente_unico',
            )
        ]


class Firma(models.Model):
    """Firma electrónica: quién firmó la orden, con qué rol y cuándo."""
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='firmas')
    rol = models.CharField(max_length=20)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['orden', 'rol'], name='una_firma_por_rol')]
        ordering = ['fecha']


class HistorialOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=15, blank=True)
    estado_nuevo = models.CharField(max_length=15)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
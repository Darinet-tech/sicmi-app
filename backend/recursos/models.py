from django.conf import settings
from django.db import models
from django.db.models import Max

from accounts.models import UnidadOrganizativa


class Almacen(models.Model):
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='almacenes')
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name_plural = 'Almacenes'
        ordering = ['uo', 'codigo']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'codigo'], name='almacen_unico_por_uo')
        ]

    def __str__(self):
        return f'{self.codigo} {self.nombre}'.strip()


class Material(models.Model):
    """Material del catálogo SAP (el código es único en toda la empresa)."""
    codigo_sap = models.CharField(max_length=40, unique=True)
    descripcion = models.CharField(max_length=255)
    unidad_medida = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ['descripcion']

    def __str__(self):
        return f'{self.codigo_sap} - {self.descripcion}'


class Existencia(models.Model):
    """Stock en libre utilización de un material en un almacén."""
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='existencias')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='existencias')
    cantidad_libre = models.DecimalField(max_digits=14, decimal_places=3)
    valor_unitario = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Existencias'
        constraints = [
            models.UniqueConstraint(fields=['almacen', 'material'], name='existencia_unica')
        ]

    def __str__(self):
        return f'{self.material.codigo_sap} en {self.almacen}: {self.cantidad_libre}'


class PresupuestoAnual(models.Model):
    """Financiamiento asignado a la UO para mantenimiento por medios propios (lo da el Área Rectora)."""
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='presupuestos')
    anio = models.PositiveSmallIntegerField('Año')
    monto = models.DecimalField('Monto asignado (CUP)', max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'Presupuesto anual'
        verbose_name_plural = 'Presupuestos anuales'
        ordering = ['-anio', 'uo']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'anio'], name='presupuesto_unico_por_uo_anio')
        ]

    def __str__(self):
        return f'{self.uo.acronimo} {self.anio}: {self.monto}'


class Sobregiro(models.Model):
    """Anexos 4 y 5: solicitud y aprobación de sobregiro."""

    class Estado(models.TextChoices):
        SOLICITADO = 'SOLICITADO', 'Solicitado'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='sobregiros')
    anio = models.PositiveSmallIntegerField()
    # Datos del Anexo 4 al momento de la solicitud
    financiamiento_asignado = models.DecimalField(max_digits=14, decimal_places=2)
    real_gastado = models.DecimalField(max_digits=14, decimal_places=2)
    monto_solicitado = models.DecimalField(max_digits=14, decimal_places=2)
    fundamentacion = models.TextField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.SOLICITADO)
    # Datos del Anexo 5
    monto_aprobado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    respuesta = models.TextField(blank=True)
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    creado = models.DateTimeField(auto_now_add=True)
    resuelto = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f'Sobregiro {self.uo.acronimo} {self.anio} ({self.get_estado_display()})'


class SolicitudRecurso(models.Model):
    """Anexo 3 - Modelo de solicitud de recursos (materiales) para una orden de trabajo."""

    class Estado(models.TextChoices):
        SOLICITADA = 'SOLICITADA', 'Solicitada'
        PENDIENTE_SOBREGIRO = 'PENDIENTE_SOBREGIRO', 'Pendiente de sobregiro'
        VERIFICADA = 'VERIFICADA', 'Verificada'
        AUTORIZADA = 'AUTORIZADA', 'Autorizada'
        DESPACHADA = 'DESPACHADA', 'Despachada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='solicitudes_recursos')
    anio = models.PositiveSmallIntegerField()
    numero = models.PositiveIntegerField()
    orden = models.ForeignKey('ordenes.Orden', on_delete=models.PROTECT, related_name='solicitudes_recursos')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='solicitudes')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.SOLICITADA)

    solicitada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    creada = models.DateTimeField(auto_now_add=True)
    verificada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    autorizada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    fecha_autorizacion = models.DateTimeField(null=True, blank=True)
    despachada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    fecha_despacho = models.DateTimeField(null=True, blank=True)
    vale_numero = models.CharField('No. de vale de salida', max_length=30, blank=True)
    motivo = models.TextField('Motivo de rechazo o cancelación', blank=True)

    class Meta:
        verbose_name = 'Solicitud de recursos'
        verbose_name_plural = 'Solicitudes de recursos'
        ordering = ['-anio', '-numero']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'anio', 'numero'], name='solicitud_recurso_consecutivo_unico')
        ]

    @property
    def codigo(self):
        return f'R-{self.anio % 100:02d}-{self.numero:03d}'

    @classmethod
    def siguiente_numero(cls, uo, anio):
        ultimo = cls.objects.filter(uo=uo, anio=anio).aggregate(m=Max('numero'))['m'] or 0
        return ultimo + 1

    def __str__(self):
        return f'{self.codigo} ({self.uo.acronimo})'


class LineaRecurso(models.Model):
    solicitud = models.ForeignKey(SolicitudRecurso, on_delete=models.CASCADE, related_name='lineas')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='lineas')
    cantidad = models.DecimalField('Cantidad solicitada', max_digits=14, decimal_places=3)
    cantidad_despachada = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['solicitud', 'material'], name='material_unico_por_solicitud')
        ]
from django.conf import settings
from django.db import models
from django.db.models import Q

from accounts.models import UnidadOrganizativa


class Trabajador(models.Model):
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='trabajadores')
    nombre = models.CharField('Nombre y apellidos', max_length=150)
    cargo = models.CharField(max_length=100, blank=True)
    # Opcional: muchos operarios nunca iniciarán sesión en el sistema
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='trabajador',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Trabajadores'
        ordering = ['uo', 'nombre']

    def __str__(self):
        return self.nombre


class EstadoDiario(models.Model):
    """Estado de un trabajador en una fecha (el historial nunca se sobrescribe)."""

    class Estado(models.TextChoices):
        TRABAJANDO = 'TRABAJANDO', 'Trabajando'
        VACACIONES = 'VACACIONES', 'Vacaciones'
        ENFERMO = 'ENFERMO', 'Enfermo'
        FUERA = 'FUERA', 'Trabajando fuera'
        CURSO = 'CURSO', 'Curso'
        AUSENTE = 'AUSENTE', 'Ausente'

    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='estados')
    fecha = models.DateField()
    estado = models.CharField(max_length=15, choices=Estado.choices)
    observacion = models.CharField(max_length=200, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado diario'
        verbose_name_plural = 'Estados diarios'
        ordering = ['-fecha']
        constraints = [
            models.UniqueConstraint(fields=['trabajador', 'fecha'], name='estado_unico_por_dia')
        ]

    def __str__(self):
        return f'{self.trabajador} {self.fecha}: {self.get_estado_display()}'


class Brigada(models.Model):
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='brigadas')
    nombre = models.CharField(max_length=100)
    jefe = models.ForeignKey(
        Trabajador, null=True, blank=True, on_delete=models.SET_NULL, related_name='brigadas_que_dirige'
    )
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['uo', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'nombre'], name='brigada_unica_por_uo')
        ]

    def __str__(self):
        return self.nombre


class MiembroBrigada(models.Model):
    """Pertenencia de un trabajador a una brigada, con fechas (hasta vacío = vigente)."""
    brigada = models.ForeignKey(Brigada, on_delete=models.CASCADE, related_name='miembros')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='membresias')
    desde = models.DateField()
    hasta = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Miembro de brigada'
        verbose_name_plural = 'Miembros de brigadas'
        constraints = [
            # Un trabajador solo puede tener UNA membresía vigente
            models.UniqueConstraint(
                fields=['trabajador'], condition=Q(hasta__isnull=True),
                name='una_brigada_vigente_por_trabajador',
            )
        ]
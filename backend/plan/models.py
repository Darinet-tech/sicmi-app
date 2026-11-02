from django.conf import settings
from django.db import models

from accounts.models import UnidadOrganizativa
from catalogos.models import GrupoGenerico, Inmueble


class PlanAnual(models.Model):
    """REG.4 - Plan Anual de Mantenimiento Preventivo con Medios Propios (Anexo 9)."""

    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'En elaboración'
        EN_FIRMAS = 'EN_FIRMAS', 'En revisión y firmas'
        APROBADO = 'APROBADO', 'Aprobado'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='planes')
    anio = models.PositiveSmallIntegerField('Año del plan')
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BORRADOR)
    elaborado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    motivo_devolucion = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plan anual preventivo'
        verbose_name_plural = 'Planes anuales preventivos'
        ordering = ['-anio', 'uo']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'anio'], name='plan_unico_por_uo_anio')
        ]

    def __str__(self):
        return f'Plan {self.anio} · {self.uo.acronimo}'


class AccionPlan(models.Model):
    """Una obra del plan: un grupo genérico de acciones en un inmueble."""

    class Via(models.TextChoices):
        PROPIOS = 'PROPIOS', 'Medios propios'
        TERCEROS = 'TERCEROS', 'Con terceros'
        INVERSION = 'INVERSION', 'Tarea de inversión'

    plan = models.ForeignKey(PlanAnual, on_delete=models.CASCADE, related_name='acciones')
    inmueble = models.ForeignKey(Inmueble, on_delete=models.PROTECT, related_name='acciones_plan')
    grupo = models.ForeignKey(GrupoGenerico, on_delete=models.PROTECT, related_name='acciones_plan')
    descripcion = models.TextField(blank=True)
    via = models.CharField(max_length=10, choices=Via.choices, default=Via.PROPIOS)
    # 1 vulnerabilidades · 2 filtraciones y humedad · 3 clima y eficiencia energética · 4 imagen
    prioridad = models.PositiveSmallIntegerField(default=4)
    es_compleja = models.BooleanField('Obra de mantenimiento compleja', default=False)
    # {"3": 2, "7": 1} = 2 acciones en marzo y 1 en julio
    programacion = models.JSONField(default=dict, blank=True)
    valor_estimado = models.DecimalField('Valor estimado (MCUP)', max_digits=12, decimal_places=3, default=0)

    class Meta:
        verbose_name = 'Obra del plan'
        verbose_name_plural = 'Obras del plan'
        ordering = ['inmueble__denominacion', 'grupo__numero', 'id']

    @property
    def cantidad(self):
        return sum(int(v) for v in self.programacion.values())

    def __str__(self):
        return f'{self.inmueble} · {self.grupo}'


class TareaTecnica(models.Model):
    """Anexo 7."""
    accion = models.OneToOneField(AccionPlan, on_delete=models.CASCADE, related_name='tarea_tecnica')
    descripcion_general = models.TextField(blank=True)
    # [{"desperfecto": "", "trabajo": "", "um": "", "cantidad": ""}]
    trabajos = models.JSONField(default=list)
    elaborado_nombre = models.CharField(max_length=150, blank=True)
    elaborado_cargo = models.CharField(max_length=150, blank=True)
    actualizado = models.DateTimeField(auto_now=True)


class Croquis(models.Model):
    """Anexo 8: imagen del croquis o plano con su cajetín."""
    accion = models.OneToOneField(AccionPlan, on_delete=models.CASCADE, related_name='croquis')
    imagen = models.ImageField(upload_to='croquis/')
    plano_no = models.CharField(max_length=30, blank=True)
    escala = models.CharField(max_length=30, blank=True)
    fecha = models.DateField(null=True, blank=True)
    proyecto = models.CharField(max_length=150, blank=True)
    plano = models.CharField(max_length=150, blank=True)
    elaborado = models.CharField(max_length=100, blank=True)
    proyectado = models.CharField(max_length=100, blank=True)
    aprobado = models.CharField(max_length=100, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Croquis'


class PlanFirma(models.Model):
    plan = models.ForeignKey(PlanAnual, on_delete=models.CASCADE, related_name='firmas')
    rol = models.CharField(max_length=20)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
        constraints = [models.UniqueConstraint(fields=['plan', 'rol'], name='una_firma_plan_por_rol')]


class HistorialPlan(models.Model):
    plan = models.ForeignKey(PlanAnual, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
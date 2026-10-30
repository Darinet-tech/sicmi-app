from django.db import models
from accounts.models import UnidadOrganizativa


class GrupoGenerico(models.Model):
    """Los 20 grupos genéricos de acciones constructivas (compartidos por toda la empresa).
    También se usan como lista de 'Afectaciones' en las solicitudes."""
    numero = models.PositiveSmallIntegerField(unique=True)
    nombre = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'Grupo genérico'
        verbose_name_plural = 'Grupos genéricos'
        ordering = ['numero']

    def __str__(self):
        return f'{self.numero}. {self.nombre}'


class Inmueble(models.Model):
    """Inmueble según el inventario GESIN. Pertenece a una UO."""
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='inmuebles')
    denominacion = models.CharField('Denominación (según GESIN)', max_length=200)
    direccion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['uo', 'denominacion']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'denominacion'], name='inmueble_unico_por_uo')
        ]

    def __str__(self):
        return self.denominacion


class CentroCosto(models.Model):
    """Centro de costo al que se carga el gasto del mantenimiento."""
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='centros_costo')
    codigo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Centro de costo'
        verbose_name_plural = 'Centros de costo'
        ordering = ['uo', 'codigo']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'codigo'], name='centro_costo_unico_por_uo')
        ]

    def __str__(self):
        return f'{self.codigo} {self.nombre}'.strip()


class Departamento(models.Model):
    """Departamentos de la UO (para la ficha del trabajador)."""
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='departamentos')
    nombre = models.CharField(max_length=100)

    class Meta:
        ordering = ['uo', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'nombre'], name='departamento_unico_por_uo')
        ]

    def __str__(self):
        return f'{self.uo.acronimo} · {self.nombre}'


class CentroTelefonico(models.Model):
    """Centros telefónicos principales (CT_NG) y asociados (CTA_NG)."""

    class Tipo(models.TextChoices):
        PRINCIPAL = 'PRINCIPAL', 'Centro telefónico principal'
        ASOCIADO = 'ASOCIADO', 'Centro telefónico asociado (CTA)'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='centros_telefonicos')
    codigo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=120, blank=True)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)

    class Meta:
        verbose_name = 'Centro telefónico'
        verbose_name_plural = 'Centros telefónicos'
        ordering = ['uo', 'tipo', 'codigo']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'codigo'], name='centro_telefonico_unico_por_uo')
        ]

    def __str__(self):
        return f'{self.uo.acronimo} · {self.codigo} ({self.get_tipo_display()})'


class AreaSolicitante(models.Model):
    """Áreas que solicitan servicios: departamentos, grupos, oficinas comerciales, minipuntos..."""
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='areas_solicitantes')
    nombre = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'Área solicitante'
        verbose_name_plural = 'Áreas solicitantes'
        ordering = ['uo', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'nombre'], name='area_unica_por_uo')
        ]

    def __str__(self):
        return f'{self.uo.acronimo} · {self.nombre}'


class Local(models.Model):
    """Local o espacio dentro de un inmueble (donde ocurre la incidencia)."""
    inmueble = models.ForeignKey(Inmueble, on_delete=models.PROTECT, related_name='locales')
    nombre = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Locales'
        ordering = ['inmueble', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['inmueble', 'nombre'], name='local_unico_por_inmueble')
        ]

    def __str__(self):
        return f'{self.inmueble} · {self.nombre}'
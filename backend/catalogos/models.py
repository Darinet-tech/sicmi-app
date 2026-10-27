from django.db import models
from accounts.models import UnidadOrganizativa


class GrupoGenerico(models.Model):
    """Los 20 grupos genéricos de acciones constructivas (compartidos por toda la empresa)."""
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
            models.UniqueConstraint(
                fields=['uo', 'denominacion'], name='inmueble_unico_por_uo'
            )
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
            models.UniqueConstraint(
                fields=['uo', 'codigo'], name='centro_costo_unico_por_uo'
            )
        ]

    def __str__(self):
        return f'{self.codigo} {self.nombre}'.strip()
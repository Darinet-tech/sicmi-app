from django.db import models
from accounts.models import UnidadOrganizativa


class Almacen(models.Model):
    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='almacenes')
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name_plural = 'Almacénes'
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
        verbose_name_plural = 'Materiales'
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
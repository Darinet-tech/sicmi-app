from django.conf import settings
from django.db import models


class UnidadOrganizativa(models.Model):
    """Unidad Organizativa (UO) de la empresa. Separa los datos por territorio o área."""
    nombre = models.CharField(max_length=120, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Unidad Organizativa'
        verbose_name_plural = 'Unidades Organizativas'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Perfil(models.Model):
    """Datos adicionales del usuario: su UO y su cargo."""

    class Rol(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente (directivo del área)'
        JEFE_BRIGADA = 'JEFE_BRIGADA', 'Jefe de Brigada'
        OPERARIO = 'OPERARIO', 'Operario de mantenimiento'
        JEFE_GRUPO = 'JEFE_GRUPO', 'Jefe de Grupo de Servicios'
        ESPECIALISTA = 'ESPECIALISTA', 'Especialista en Obras de Ingenierías'
        JEFE_LOGISTICA = 'JEFE_LOGISTICA', 'Jefe de Departamento o Director de Logística y Servicios'
        BALANCISTA = 'BALANCISTA', 'Balancista Distribuidor'
        DIRECTOR_UO = 'DIRECTOR_UO', 'Director de la UO'
        CENTRAL = 'CENTRAL', 'Nivel central (Inmobiliaria / DVLS)'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil'
    )
    uo = models.ForeignKey(
        UnidadOrganizativa, null=True, blank=True,
        on_delete=models.PROTECT, related_name='perfiles',
        help_text='Vacío solo para usuarios de nivel central.',
    )
    rol = models.CharField(max_length=20, choices=Rol.choices)
    cargo = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} ({self.get_rol_display()})'

    @property
    def es_central(self):
        return self.rol == self.Rol.CENTRAL
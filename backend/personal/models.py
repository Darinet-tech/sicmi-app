from django.conf import settings
from django.db import models
from django.db.models import Q

from accounts.models import UnidadOrganizativa
from django.core.validators import RegexValidator


LETRAS = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]


class Trabajador(models.Model):
    class Cargo(models.TextChoices):
        AYUDANTE = 'AYUDANTE', 'Ayudante'
        OPERARIO = 'OPERARIO', 'Operario'
        JEFE_BRIGADA = 'JEFE_BRIGADA', 'Jefe de Brigada'
        ESPECIALISTA = 'ESPECIALISTA', 'Especialista en Obras de Ingeniería'
        JEFE_DEPARTAMENTO = 'JEFE_DEPARTAMENTO', 'Jefe de Departamento'
        JEFE_SERVICIOS = 'JEFE_SERVICIOS', 'Jefe de Servicios'

    class NivelEscolar(models.TextChoices):
        NOVENO = 'NOVENO', '9no grado'
        DOCE = 'DOCE', '12 grado'
        TECNICO = 'TECNICO', 'Técnico medio'
        OBRERO = 'OBRERO', 'Obrero calificado'
        UNIVERSITARIO = 'UNIVERSITARIO', 'Universitario'

    uo = models.ForeignKey(UnidadOrganizativa, on_delete=models.PROTECT, related_name='trabajadores')

    # Identificación
    codigo = models.CharField('Código', max_length=20)
    nombre = models.CharField('Nombre y apellidos', max_length=150)
    carnet_identidad = models.CharField(
        'Carnet de identidad', max_length=11, unique=True,
        validators=[RegexValidator(r'^\d{11}$', 'El carnet de identidad debe tener 11 dígitos.')],
    )
    nivel_escolar = models.CharField(max_length=15, choices=NivelEscolar.choices)
    direccion = models.CharField('Dirección particular', max_length=255)

    # Puesto
    cargo = models.CharField(max_length=20, choices=Cargo.choices)
    categoria = models.CharField('Categoría', max_length=1, choices=LETRAS)
    departamento = models.CharField(max_length=100)
    centro_principal = models.CharField('Centro principal', max_length=30)
    centro_asociado = models.CharField('Centro asociado', max_length=30, blank=True)
    numero_plaza = models.CharField('No. de plaza', max_length=20)
    salario = models.DecimalField(max_digits=10, decimal_places=2)

    # Licencia de conducción (el número y la categoría solo si tiene licencia)
    licencia_conduccion = models.BooleanField('Licencia de conducción', default=False)
    numero_licencia = models.CharField('No. de licencia', max_length=30, blank=True)
    categoria_licencia = models.CharField('Categoría de la licencia', max_length=1, choices=LETRAS, blank=True)

    # Contacto (opcional)
    movil = models.CharField('Móvil', max_length=20, blank=True)
    telefono_particular = models.CharField('Teléfono particular', max_length=20, blank=True)
    telefono_oficina = models.CharField('Teléfono de oficina', max_length=20, blank=True)

    # Opcional: solo si el trabajador también tiene usuario en el sistema
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='trabajador',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Trabajadores'
        ordering = ['uo', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['uo', 'codigo'], name='trabajador_codigo_unico_por_uo')
        ]

    def __str__(self):
        return f'{self.codigo} {self.nombre}'


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
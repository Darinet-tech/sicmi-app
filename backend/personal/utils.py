from .models import EstadoDiario


def estado_trabajador(trabajador, fecha):
    """Último estado registrado hasta esa fecha (si no hay ninguno, se asume Trabajando)."""
    reg = EstadoDiario.objects.filter(trabajador=trabajador, fecha__lte=fecha).order_by('-fecha').first()
    return reg.estado if reg else EstadoDiario.Estado.TRABAJANDO
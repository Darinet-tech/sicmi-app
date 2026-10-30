from .models import EstadoVehiculo


def estado_vehiculo(vehiculo, fecha):
    """Último estado registrado hasta esa fecha (si no hay ninguno, se asume Disponible)."""
    reg = EstadoVehiculo.objects.filter(vehiculo=vehiculo, fecha__lte=fecha).order_by('-fecha').first()
    return reg.estado if reg else EstadoVehiculo.Estado.DISPONIBLE
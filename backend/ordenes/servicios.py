from django.utils import timezone

from personal.models import EstadoDiario, MiembroBrigada
from personal.utils import estado_trabajador
from .models import BrigadaOrden, ParticipanteOrden


def agregar_brigada_a_orden(orden, brigada, usuario):
    """Agrega la brigada y a sus miembros que hoy figuren como Trabajando. Devuelve avisos."""
    hoy = timezone.localdate()
    avisos = []
    BrigadaOrden.objects.create(orden=orden, brigada=brigada, desde=hoy)

    ya_participan = set(
        orden.participantes.filter(hasta__isnull=True).values_list('trabajador_id', flat=True)
    )
    miembros = MiembroBrigada.objects.filter(
        brigada=brigada, hasta__isnull=True, trabajador__activo=True
    ).select_related('trabajador')

    for m in miembros:
        t = m.trabajador
        if t.id in ya_participan:
            continue
        estado = estado_trabajador(t, hoy)
        if estado != EstadoDiario.Estado.TRABAJANDO:
            avisos.append(f'{t.nombre} no se agregó: hoy figura como {EstadoDiario.Estado(estado).label}.')
            continue
        ParticipanteOrden.objects.create(
            orden=orden, trabajador=t, brigada=brigada, desde=hoy,
            motivo='Miembro de la brigada', agregado_por=usuario,
        )
    return avisos


def cerrar_brigada(orden, brigada):
    """Pone fecha de fin a la brigada y a los participantes que vinieron con ella."""
    hoy = timezone.localdate()
    orden.brigadas.filter(brigada=brigada, hasta__isnull=True).update(hasta=hoy)
    orden.participantes.filter(brigada=brigada, hasta__isnull=True).update(hasta=hoy)
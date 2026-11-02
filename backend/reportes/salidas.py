from datetime import date

from django.utils import timezone

from accounts.models import Perfil
from .calculos import MESES, filas_certificacion
from .models import Certificacion
from .reglas import acciones_permitidas, proxima_firma

ROLES = dict(Perfil.Rol.choices)


def nombre(u):
    return (u.get_full_name() or u.username) if u else ''


def limite(anio, mes):
    """Plazo de envío: antes del día 5 del mes siguiente."""
    return date(anio + 1, 1, 5) if mes == 12 else date(anio, mes + 1, 5)


def salida_cert(c, user, detalle=True):
    filas, resumen = filas_certificacion(c)
    lim = limite(c.anio, c.mes)
    hoy = timezone.localdate()
    datos = {
        'id': c.id, 'anio': c.anio, 'mes': c.mes, 'mes_nombre': MESES[c.mes - 1],
        'uo_acronimo': c.uo.acronimo, 'estado': c.estado, 'estado_display': c.get_estado_display(),
        'resumen': resumen, 'limite': lim,
        'vencida': hoy > lim and c.estado != Certificacion.Estado.APROBADA,
        'mes_en_curso': (c.anio, c.mes) == (hoy.year, hoy.month),
    }
    if not detalle:
        return datos
    datos.update({
        'filas': filas,
        'indicadores': (c.datos or {}).get('indicadores'),
        'generada': (c.datos or {}).get('generada'),
        'motivo_devolucion': c.motivo_devolucion,
        'firmas': [{'rol': f.rol, 'rol_display': ROLES.get(f.rol, f.rol), 'usuario': nombre(f.usuario),
                    'fecha': f.fecha} for f in c.firmas.all()],
        'proxima_firma': proxima_firma(c) if c.estado == Certificacion.Estado.EN_FIRMAS else None,
        'acciones_permitidas': acciones_permitidas(c, user),
        'historial': [{'usuario': nombre(h.usuario), 'comentario': h.comentario, 'fecha': h.fecha}
                      for h in c.historial.all()],
    })
    return datos
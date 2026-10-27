from accounts.models import Perfil
from .models import Solicitud

E = Solicitud.Estado
R = Perfil.Rol

# (estado_actual, estado_nuevo): roles que pueden hacer ese cambio
TRANSICIONES = {
    (E.ENVIADA, E.EN_REVISION): {R.JEFE_LOGISTICA, R.JEFE_GRUPO},
    (E.EN_REVISION, E.DEVUELTA): {R.JEFE_LOGISTICA, R.JEFE_GRUPO},
    (E.EN_REVISION, E.EN_INSPECCION): {R.JEFE_LOGISTICA, R.JEFE_GRUPO},
    (E.DEVUELTA, E.ENVIADA): {R.CLIENTE},
    (E.EN_INSPECCION, E.EN_PROGRAMACION): {R.JEFE_BRIGADA, R.ESPECIALISTA},
    (E.EN_PROGRAMACION, E.ORDEN_GENERADA): {R.ESPECIALISTA},
    (E.ORDEN_GENERADA, E.CERRADA): {R.ESPECIALISTA},
}

ROLES_CANCELAN = {R.JEFE_LOGISTICA, R.JEFE_GRUPO, R.ESPECIALISTA}


def puede_transicionar(solicitud, nuevo_estado, perfil):
    """Devuelve True si el perfil puede mover la solicitud al nuevo estado."""
    if nuevo_estado == E.CANCELADA:
        if solicitud.estado in (E.CERRADA, E.CANCELADA):
            return False
        es_dueño = perfil.rol == R.CLIENTE and solicitud.solicitante_id == perfil.usuario_id
        return perfil.rol in ROLES_CANCELAN or es_dueño
    roles = TRANSICIONES.get((solicitud.estado, nuevo_estado))
    return roles is not None and perfil.rol in roles
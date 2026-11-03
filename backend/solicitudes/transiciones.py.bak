from accounts.models import Perfil
from .models import Solicitud

E = Solicitud.Estado
R = Perfil.Rol

# (estado_actual, estado_nuevo): roles que pueden hacer ese cambio.
# ORDEN_GENERADA y CERRADA ya no están aquí: los controla la Orden de Trabajo.
TRANSICIONES = {
    (E.ENVIADA, E.EN_REVISION): {R.JEFE_LOGISTICA, R.JEFE_GRUPO},
    (E.EN_REVISION, E.DEVUELTA): {R.JEFE_LOGISTICA, R.JEFE_GRUPO},
    (E.EN_REVISION, E.EN_INSPECCION): {R.JEFE_LOGISTICA, R.JEFE_GRUPO},
    (E.DEVUELTA, E.ENVIADA): {R.CLIENTE},
    (E.EN_INSPECCION, E.EN_PROGRAMACION): {R.JEFE_BRIGADA, R.ESPECIALISTA},
}

ROLES_CANCELAN = {R.JEFE_LOGISTICA, R.JEFE_GRUPO, R.ESPECIALISTA}


def puede_transicionar(solicitud, nuevo_estado, perfil):
    """Devuelve True si el perfil puede mover la solicitud al nuevo estado."""
    if nuevo_estado == E.CANCELADA:
        # Con orden generada, se cancela la orden (eso cancela también la solicitud)
        if solicitud.estado in (E.CERRADA, E.CANCELADA, E.ORDEN_GENERADA):
            return False
        es_dueño = perfil.rol == R.CLIENTE and solicitud.solicitante_id == perfil.usuario_id
        return perfil.rol in ROLES_CANCELAN or es_dueño
    roles = TRANSICIONES.get((solicitud.estado, nuevo_estado))
    return roles is not None and perfil.rol in roles
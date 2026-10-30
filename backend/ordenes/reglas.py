from accounts.models import Perfil
from .models import Orden

R = Perfil.Rol
E = Orden.Estado

# Se usan los valores de texto (.value) para poder compararlos con lo guardado en la base de datos
ROLES_TRABAJO = {R.ESPECIALISTA.value, R.JEFE_BRIGADA.value}
ROLES_CANCELAN = {R.ESPECIALISTA.value, R.JEFE_GRUPO.value}
# Orden en que firman tras la conformidad del cliente (según el procedimiento)
CADENA_FIRMAS = [R.JEFE_BRIGADA.value, R.JEFE_GRUPO.value, R.ESPECIALISTA.value]
ABIERTAS = (E.REGISTRADA, E.EN_EJECUCION)


def proxima_firma(orden):
    """Rol que debe firmar a continuación, o None si ya firmaron todos."""
    firmados = {f.rol for f in orden.firmas.all()}
    for rol in CADENA_FIRMAS:
        if rol not in firmados:
            return rol
    return None


def acciones_permitidas(orden, user):
    rol = user.perfil.rol
    acciones = []
    if rol in ROLES_TRABAJO and orden.estado in ABIERTAS:
        acciones.append('editar')  # datos, participantes y brigadas
        if orden.estado == E.REGISTRADA:
            acciones.append('iniciar')
        if orden.estado == E.EN_EJECUCION:
            acciones.append('entregar')
    if rol == R.CLIENTE and orden.estado == E.ENTREGADA and orden.cliente_id == user.id:
        acciones.append('conformidad')
    if orden.estado == E.CONFORME and proxima_firma(orden) == rol:
        acciones.append('firmar')
    if rol in ROLES_CANCELAN and orden.estado not in (E.CERRADA, E.CANCELADA):
        acciones.append('cancelar')
    return acciones
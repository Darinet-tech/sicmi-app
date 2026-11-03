from accounts.models import Perfil
from recursos.models import SolicitudRecurso
from .models import Orden

R = Perfil.Rol
E = Orden.Estado
S = SolicitudRecurso.Estado

# Se usan los valores de texto (.value) para poder compararlos con lo guardado en la base de datos
ROLES_TRABAJO = {R.ESPECIALISTA.value, R.JEFE_BRIGADA.value}
ROLES_CANCELAN = {R.ESPECIALISTA.value, R.JEFE_GRUPO.value}
# Orden en que firman tras la conformidad del cliente (según el procedimiento)
CADENA_FIRMAS = [R.JEFE_BRIGADA.value, R.JEFE_GRUPO.value, R.ESPECIALISTA.value]
ABIERTAS = (E.EN_PROCESO, E.REGISTRADA, E.EN_EJECUCION)


def proxima_firma(orden):
    """Rol que debe firmar a continuación, o None si ya firmaron todos."""
    firmados = {f.rol for f in orden.firmas.all()}
    for rol in CADENA_FIRMAS:
        if rol not in firmados:
            return rol
    return None


def requisitos(orden):
    """Requisitos para generar la orden: lista de (texto, cumplido)."""
    activas = [s for s in orden.solicitudes_recursos.all() if s.estado not in (S.CANCELADA, S.RECHAZADA)]
    con_vale = [s for s in activas if s.estado == S.DESPACHADA and s.vale_numero]
    pendientes = [s for s in activas if s.estado != S.DESPACHADA]

    items = [
        ('Inspección registrada', bool(orden.inspeccion_por.strip())),
        ('Al menos un participante asignado', orden.participantes.filter(hasta__isnull=True).exists()),
    ]
    if orden.sin_materiales:
        items.append(('No hay solicitudes de recursos activas (la orden no requiere materiales)', not activas))
    else:
        items.append(('Solicitud de recursos despachada, con número de vale de salida', bool(con_vale)))
        items.append(('No quedan solicitudes de recursos pendientes de despacho', not pendientes))
    return items


def acciones_permitidas(orden, user):
    rol = user.perfil.rol
    acciones = []
    if rol in ROLES_TRABAJO and orden.estado in ABIERTAS:
        acciones.append('editar')  # datos, participantes y brigadas
    if rol == R.ESPECIALISTA.value and orden.estado == E.EN_PROCESO:
        acciones.append('generar')
    if rol in ROLES_TRABAJO and orden.estado == E.REGISTRADA:
        acciones.append('iniciar')
    if rol in ROLES_TRABAJO and orden.estado == E.EN_EJECUCION:
        acciones.append('entregar')
    if rol == R.CLIENTE.value and orden.estado == E.ENTREGADA and orden.cliente_id == user.id:
        acciones.append('conformidad')
    if orden.estado == E.CONFORME and proxima_firma(orden) == rol:
        acciones.append('firmar')
    if rol in ROLES_CANCELAN and orden.estado not in (E.CERRADA, E.CANCELADA):
        acciones.append('cancelar')
    return acciones
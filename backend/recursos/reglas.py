from accounts.models import Perfil
from .models import SolicitudRecurso

R = Perfil.Rol
S = SolicitudRecurso.Estado

ROLES_CREAN = {R.ESPECIALISTA.value, R.JEFE_BRIGADA.value}
ROLES_DESPACHAN = {R.BALANCISTA.value, R.JEFE_BRIGADA.value}
ROLES_SOBRANTES = {R.ESPECIALISTA.value, R.JEFE_BRIGADA.value, R.BALANCISTA.value}
ABIERTAS = (S.SOLICITADA, S.PENDIENTE_SOBREGIRO, S.VERIFICADA, S.AUTORIZADA)
ORDEN_TERMINADA = ('CERRADA', 'CANCELADA')


def acciones_recurso(sol, user):
    rol = user.perfil.rol
    a = []
    if rol == R.ESPECIALISTA.value and sol.estado in (S.SOLICITADA, S.PENDIENTE_SOBREGIRO):
        a.append('verificar')
    if rol == R.JEFE_LOGISTICA.value and sol.estado == S.VERIFICADA:
        a += ['autorizar', 'rechazar']
    if rol in ROLES_DESPACHAN and sol.estado == S.AUTORIZADA:
        a.append('despachar')
    if sol.estado in ABIERTAS and (rol == R.ESPECIALISTA.value or sol.solicitada_por_id == user.id):
        a.append('cancelar')
    # Sobrantes: mientras la orden siga abierta
    if sol.estado == S.DESPACHADA and rol in ROLES_SOBRANTES and sol.orden.estado not in ORDEN_TERMINADA:
        a.append('sobrante')
        if not sol.sobrantes_revisados:
            a.append('revisar_sobrantes')
    return a
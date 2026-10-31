from accounts.models import Perfil
from .models import SolicitudRecurso

R = Perfil.Rol
S = SolicitudRecurso.Estado

ROLES_CREAN = {R.ESPECIALISTA.value, R.JEFE_BRIGADA.value}
ROLES_DESPACHAN = {R.BALANCISTA.value, R.JEFE_BRIGADA.value}
ABIERTAS = (S.SOLICITADA, S.PENDIENTE_SOBREGIRO, S.VERIFICADA, S.AUTORIZADA)


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
    return a
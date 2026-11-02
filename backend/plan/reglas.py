from accounts.models import Perfil
from .models import PlanAnual

R = Perfil.Rol
P = PlanAnual.Estado

# Quién firma y en qué orden (numeral 7.2.1 del procedimiento)
CADENA = [R.ESPECIALISTA.value, R.JEFE_GRUPO.value, R.JEFE_LOGISTICA.value, R.DIRECTOR_UO.value]
ROLES_VEN = {R.ESPECIALISTA.value, R.JEFE_BRIGADA.value, R.JEFE_GRUPO.value,
             R.JEFE_LOGISTICA.value, R.DIRECTOR_UO.value, R.CENTRAL.value}


def proxima_firma(plan):
    """Rol que debe firmar a continuación, o None si ya firmaron todos."""
    firmados = {f.rol for f in plan.firmas.all()}
    for rol in CADENA:
        if rol not in firmados:
            return rol
    return None


def acciones_permitidas(plan, user):
    rol = user.perfil.rol
    a = []
    if rol == R.ESPECIALISTA.value:
        if plan.estado == P.BORRADOR:
            a += ['editar', 'enviar']
        if plan.estado in (P.BORRADOR, P.APROBADO):
            a.append('tecnica')
        if plan.estado == P.APROBADO:
            a.append('generar')
    if plan.estado == P.EN_FIRMAS and proxima_firma(plan) == rol:
        a += ['firmar', 'devolver']
    return a
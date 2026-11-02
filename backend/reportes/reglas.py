from accounts.models import Perfil
from .models import Certificacion

R = Perfil.Rol
C = Certificacion.Estado

# Quién firma y en qué orden (Anexo 10)
CADENA = [R.ESPECIALISTA.value, R.JEFE_GRUPO.value, R.JEFE_LOGISTICA.value]


def proxima_firma(cert):
    """Rol que debe firmar a continuación, o None si ya firmaron todos."""
    firmados = {f.rol for f in cert.firmas.all()}
    for rol in CADENA:
        if rol not in firmados:
            return rol
    return None


def acciones_permitidas(cert, user):
    rol = user.perfil.rol
    a = []
    if rol == R.ESPECIALISTA.value and cert.estado == C.BORRADOR:
        a += ['actualizar', 'incidencias', 'enviar']
    if cert.estado == C.EN_FIRMAS and proxima_firma(cert) == rol:
        a += ['firmar', 'devolver']
    return a
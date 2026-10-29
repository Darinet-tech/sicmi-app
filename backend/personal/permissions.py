from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models import Perfil

R = Perfil.Rol
ROLES_LECTURA = {R.ESPECIALISTA, R.JEFE_BRIGADA, R.JEFE_GRUPO, R.JEFE_LOGISTICA, R.DIRECTOR_UO, R.CENTRAL}


class PersonalPermiso(BasePermission):
    """Leer: roles de gestión. Escribir: solo el Especialista."""

    def has_permission(self, request, view):
        u = request.user
        if not (u.is_authenticated and hasattr(u, 'perfil')):
            return False
        if request.method in SAFE_METHODS:
            return u.perfil.rol in ROLES_LECTURA
        return u.perfil.rol == R.ESPECIALISTA
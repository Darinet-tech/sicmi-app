from rest_framework.permissions import BasePermission

from accounts.models import Perfil

R = Perfil.Rol
ROLES_VEN = {R.ESPECIALISTA.value, R.JEFE_GRUPO.value, R.JEFE_LOGISTICA.value,
             R.DIRECTOR_UO.value, R.CENTRAL.value}


class PermisoReportes(BasePermission):
    """Mismos roles que ven el módulo Reportes en el inicio."""

    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and hasattr(u, 'perfil') and u.perfil.rol in ROLES_VEN
from rest_framework.permissions import BasePermission
from accounts.models import Perfil

R = Perfil.Rol
ROLES_RECURSOS = {R.ESPECIALISTA.value, R.JEFE_BRIGADA.value, R.BALANCISTA.value,
                  R.JEFE_LOGISTICA.value, R.DIRECTOR_UO.value, R.CENTRAL.value}
ROLES_PRESUPUESTO = {R.ESPECIALISTA.value, R.JEFE_LOGISTICA.value, R.DIRECTOR_UO.value, R.CENTRAL.value}


class _ConRoles(BasePermission):
    roles = set()

    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and hasattr(u, 'perfil') and u.perfil.rol in self.roles


class PermisoRecursos(_ConRoles):
    roles = ROLES_RECURSOS


class PermisoPresupuesto(_ConRoles):
    roles = ROLES_PRESUPUESTO
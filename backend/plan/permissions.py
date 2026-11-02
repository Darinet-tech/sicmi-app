from rest_framework.permissions import BasePermission
from .reglas import ROLES_VEN


class PermisoPlan(BasePermission):
    """Ven el plan los roles de gestión y el nivel central (el Jefe de Brigada recibe su copia)."""

    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and hasattr(u, 'perfil') and u.perfil.rol in ROLES_VEN
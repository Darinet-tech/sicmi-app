from rest_framework.permissions import BasePermission
from accounts.models import Perfil


class TienePerfil(BasePermission):
    """Solo usuarios autenticados que tengan un Perfil."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'perfil')


class PuedeCrearSolicitud(BasePermission):
    """Crear: solo Clientes. Las demás acciones las controla la vista."""
    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.perfil.rol == Perfil.Rol.CLIENTE
        return True
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView


class LoginView(TokenObtainPairView):
    """Inicio de sesión con límite de intentos (la tasa se configura en settings: 'login')."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


@api_view(['GET'])
@permission_classes([AllowAny])
def salud(request):
    """Vista de prueba para comprobar que la API responde."""
    return Response({'estado': 'ok', 'mensaje': 'La API de SiCMI funciona'})


def _perfil(request):
    if not hasattr(request.user, 'perfil'):
        raise PermissionDenied('Su usuario no tiene un perfil asignado. Contacte al administrador.')
    return request.user.perfil


@api_view(['GET'])
def yo(request):
    """Devuelve los datos del usuario autenticado."""
    p = _perfil(request)
    return Response({
        'username': request.user.username,
        'nombre': request.user.get_full_name() or request.user.username,
        'rol': p.rol,
        'rol_display': p.get_rol_display(),
        'uo': p.uo_id,
        'uo_nombre': p.uo.nombre if p.uo else None,
        'bienvenida_vista': p.bienvenida_vista,
    })


@api_view(['POST'])
def bienvenida_vista(request):
    """Marca que el usuario ya vio la pantalla de bienvenida."""
    p = _perfil(request)
    if not p.bienvenida_vista:
        p.bienvenida_vista = True
        p.save(update_fields=['bienvenida_vista'])
    return Response({'bienvenida_vista': True})
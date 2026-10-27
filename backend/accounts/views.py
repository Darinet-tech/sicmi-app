from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def salud(request):
    """Vista de prueba para comprobar que la API responde."""
    return Response({'estado': 'ok', 'mensaje': 'La API de SiCMI funciona'})
@api_view(['GET'])
def yo(request):
    """Devuelve los datos del usuario autenticado."""
    p = request.user.perfil
    return Response({
        'username': request.user.username,
        'nombre': request.user.get_full_name() or request.user.username,
        'rol': p.rol,
        'rol_display': p.get_rol_display(),
        'uo': p.uo_id,
        'uo_nombre': p.uo.nombre if p.uo else None,
    })
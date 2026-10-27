from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def salud(request):
    """Vista de prueba para comprobar que la API responde."""
    return Response({'estado': 'ok', 'mensaje': 'La API de mantenimiento funciona'})
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Perfil
from .models import Solicitud, HistorialEstado
from .permissions import TienePerfil, PuedeCrearSolicitud
from .serializers import SolicitudSerializer
from .transiciones import puede_transicionar


class SolicitudViewSet(viewsets.ModelViewSet):
    serializer_class = SolicitudSerializer
    permission_classes = [TienePerfil, PuedeCrearSolicitud]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        perfil = self.request.user.perfil
        qs = (Solicitud.objects
            .select_related('inmueble', 'solicitante', 'area_solicitante', 'local', 'afectacion')
            .prefetch_related('historial'))
        if perfil.es_central:
            return qs
        qs = qs.filter(uo=perfil.uo)
        if perfil.rol == Perfil.Rol.CLIENTE:
            qs = qs.filter(solicitante=self.request.user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        with transaction.atomic():
            solicitud = serializer.save(uo=user.perfil.uo, solicitante=user)
            HistorialEstado.objects.create(
                solicitud=solicitud, estado_nuevo=solicitud.estado, usuario=user,
                comentario='Solicitud creada',
            )

    def update(self, request, *args, **kwargs):
        """El cliente solo puede editar su solicitud mientras esté DEVUELTA."""
        solicitud = self.get_object()
        perfil = request.user.perfil
        if perfil.rol != Perfil.Rol.CLIENTE or solicitud.estado != Solicitud.Estado.DEVUELTA:
            return Response({'detalle': 'Solo el cliente puede editar una solicitud devuelta.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        solicitud = self.get_object()
        perfil = request.user.perfil
        nuevo = request.data.get('estado')
        comentario = request.data.get('comentario', '')

        if nuevo not in Solicitud.Estado.values:
            return Response({'detalle': 'Estado no válido.'}, status=status.HTTP_400_BAD_REQUEST)
        if not puede_transicionar(solicitud, nuevo, perfil):
            return Response({'detalle': 'No tiene permiso para este cambio de estado.'},
                            status=status.HTTP_403_FORBIDDEN)
        if nuevo == Solicitud.Estado.EN_PROGRAMACION and 'es_urgente' not in request.data:
            return Response({'detalle': 'Debe indicar si el trabajo es urgente o no.'},
                            status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            anterior = solicitud.estado
            solicitud.estado = nuevo
            if nuevo == Solicitud.Estado.EN_PROGRAMACION:
                solicitud.es_urgente = str(request.data['es_urgente']).lower() in ('true', '1')
            if nuevo == Solicitud.Estado.DEVUELTA:
                solicitud.motivo_devolucion = comentario
            if 'es_urgente' in request.data and nuevo == Solicitud.Estado.EN_PROGRAMACION:
                solicitud.es_urgente = bool(request.data['es_urgente'])
            solicitud.save()
            HistorialEstado.objects.create(
                solicitud=solicitud, estado_anterior=anterior, estado_nuevo=nuevo,
                usuario=request.user, comentario=comentario,
            )
        return Response(self.get_serializer(solicitud).data)
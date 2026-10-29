from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Trabajador, EstadoDiario, Brigada, MiembroBrigada
from .permissions import PersonalPermiso
from .serializers import TrabajadorSerializer, BrigadaSerializer


def de_su_uo(qs, request):
    """Cada usuario ve solo su UO (el nivel central ve todas)."""
    perfil = request.user.perfil
    return qs if perfil.es_central else qs.filter(uo=perfil.uo)


class TrabajadorViewSet(viewsets.ModelViewSet):
    serializer_class = TrabajadorSerializer
    permission_classes = [PersonalPermiso]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        return de_su_uo(Trabajador.objects.select_related('uo'), self.request)

    def perform_create(self, serializer):
        serializer.save(uo=self.request.user.perfil.uo)

    def perform_update(self, serializer):
        trabajador = serializer.save()
        if not trabajador.activo:
            # Si se desactiva, sale de su brigada
            trabajador.membresias.filter(hasta__isnull=True).update(hasta=timezone.localdate())


class BrigadaViewSet(viewsets.ModelViewSet):
    serializer_class = BrigadaSerializer
    permission_classes = [PersonalPermiso]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = Brigada.objects.select_related('uo', 'jefe').prefetch_related('miembros__trabajador')
        return de_su_uo(qs, self.request)

    def perform_create(self, serializer):
        serializer.save(uo=self.request.user.perfil.uo)

    @action(detail=True, methods=['post'])
    def agregar_miembro(self, request, pk=None):
        brigada = self.get_object()
        try:
            t = Trabajador.objects.get(pk=request.data.get('trabajador'), uo=brigada.uo, activo=True)
        except (Trabajador.DoesNotExist, ValueError, TypeError):
            return Response({'detalle': 'Trabajador no válido.'}, status=status.HTTP_400_BAD_REQUEST)

        vigente = MiembroBrigada.objects.filter(trabajador=t, hasta__isnull=True).select_related('brigada').first()
        if vigente:
            return Response(
                {'detalle': f'{t.nombre} ya pertenece a la brigada {vigente.brigada.nombre}. Quítelo primero de esa brigada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        MiembroBrigada.objects.create(brigada=brigada, trabajador=t, desde=timezone.localdate())
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=['post'])
    def quitar_miembro(self, request, pk=None):
        brigada = self.get_object()
        n = MiembroBrigada.objects.filter(
            brigada=brigada, trabajador_id=request.data.get('trabajador'), hasta__isnull=True
        ).update(hasta=timezone.localdate())
        if not n:
            return Response({'detalle': 'Ese trabajador no es miembro vigente.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(self.get_object()).data)


class PaseListaView(APIView):
    """GET: lista del día (con el último estado conocido si no se guardó). POST: guarda el día."""
    permission_classes = [PersonalPermiso]

    def get(self, request):
        fecha = parse_date(request.query_params.get('fecha', '')) or timezone.localdate()
        trabajadores = de_su_uo(
            Trabajador.objects.filter(activo=True).select_related('uo'), request
        )
        del_dia = {
            e.trabajador_id: e
            for e in EstadoDiario.objects.filter(fecha=fecha, trabajador__in=trabajadores)
        }
        filas = []
        for t in trabajadores:
            reg = del_dia.get(t.id)
            heredado = reg is None
            if heredado:  # último registro anterior a esa fecha
                reg = EstadoDiario.objects.filter(trabajador=t, fecha__lt=fecha).order_by('-fecha').first()
            filas.append({
                'trabajador': t.id,
                'nombre': t.nombre,
                'cargo': t.cargo,
                'uo': t.uo.acronimo,
                'estado': reg.estado if reg else EstadoDiario.Estado.TRABAJANDO,
                'observacion': reg.observacion if reg else '',
                'heredado': heredado,
            })
        return Response({'fecha': str(fecha), 'guardado': bool(del_dia), 'registros': filas})

    def post(self, request):
        perfil = request.user.perfil
        fecha = parse_date(str(request.data.get('fecha', '')))
        if not fecha:
            return Response({'detalle': 'Fecha no válida.'}, status=status.HTTP_400_BAD_REQUEST)
        if fecha > timezone.localdate():
            return Response({'detalle': 'No se puede registrar una fecha futura.'},
                            status=status.HTTP_400_BAD_REQUEST)
        registros = request.data.get('registros')
        if not isinstance(registros, list):
            return Response({'detalle': 'Faltan los registros.'}, status=status.HTTP_400_BAD_REQUEST)

        validos = set(EstadoDiario.Estado.values)
        permitidos = {t.id for t in Trabajador.objects.filter(uo=perfil.uo, activo=True)}
        for r in registros:  # validar todo ANTES de guardar nada
            if r.get('trabajador') not in permitidos or r.get('estado') not in validos:
                return Response({'detalle': 'Hay registros no válidos.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for r in registros:
                EstadoDiario.objects.update_or_create(
                    trabajador_id=r['trabajador'], fecha=fecha,
                    defaults={
                        'estado': r['estado'],
                        'observacion': str(r.get('observacion', ''))[:200],
                        'registrado_por': request.user,
                    },
                )
        return Response({'detalle': f'Pase de lista del {fecha} guardado.', 'total': len(registros)})
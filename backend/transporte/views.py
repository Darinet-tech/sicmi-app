from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from personal.permissions import PersonalPermiso  # mismas reglas: gestión lee, Especialista escribe
from personal.views import de_su_uo
from .models import Vehiculo, EstadoVehiculo
from .serializers import VehiculoSerializer


class VehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = VehiculoSerializer
    permission_classes = [PersonalPermiso]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        return de_su_uo(Vehiculo.objects.select_related('uo'), self.request)

    def perform_create(self, serializer):
        serializer.save(uo=self.request.user.perfil.uo)


class ParteTransporteView(APIView):
    """GET: parte del día (con el último estado conocido si no se guardó). POST: guarda el día."""
    permission_classes = [PersonalPermiso]

    def get(self, request):
        fecha = parse_date(request.query_params.get('fecha', '')) or timezone.localdate()
        vehiculos = de_su_uo(Vehiculo.objects.filter(activo=True).select_related('uo'), request)
        del_dia = {
            e.vehiculo_id: e
            for e in EstadoVehiculo.objects.filter(fecha=fecha, vehiculo__in=vehiculos)
        }
        filas = []
        for v in vehiculos:
            reg = del_dia.get(v.id)
            heredado = reg is None
            if heredado:
                reg = EstadoVehiculo.objects.filter(vehiculo=v, fecha__lt=fecha).order_by('-fecha').first()
            filas.append({
                'vehiculo': v.id,
                'chapa': v.chapa,
                'tipo': v.tipo,
                'descripcion': v.descripcion,
                'uo': v.uo.acronimo,
                'estado': reg.estado if reg else EstadoVehiculo.Estado.DISPONIBLE,
                'motivo': reg.motivo if reg else '',
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

        validos = set(EstadoVehiculo.Estado.values)
        permitidos = {v.id for v in Vehiculo.objects.filter(uo=perfil.uo, activo=True)}
        for r in registros:
            if r.get('vehiculo') not in permitidos or r.get('estado') not in validos:
                return Response({'detalle': 'Hay registros no válidos.'}, status=status.HTTP_400_BAD_REQUEST)
            if r['estado'] == EstadoVehiculo.Estado.OTRAS and not str(r.get('motivo', '')).strip():
                return Response({'detalle': 'Indique el motivo de la paralización por otras causas.'},
                                status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for r in registros:
                EstadoVehiculo.objects.update_or_create(
                    vehiculo_id=r['vehiculo'], fecha=fecha,
                    defaults={
                        'estado': r['estado'],
                        'motivo': str(r.get('motivo', '')).strip()[:200],
                        'registrado_por': request.user,
                    },
                )
        return Response({'detalle': f'Parte de transporte del {fecha} guardado.', 'total': len(registros)})

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Perfil, UnidadOrganizativa
from ordenes.models import Orden
from .models import Almacen, Existencia, LineaRecurso, Sobregiro, SolicitudRecurso
from .permissions import PermisoPresupuesto, PermisoRecursos
from .reglas import ROLES_CREAN, acciones_recurso
from .serializers import AlmacenSerializer, salida, salida_sobregiro
from .servicios import faltante, resumen_presupuesto, total_estimado

S = SolicitudRecurso.Estado
R = Perfil.Rol


class Fallo(Exception):
    """Para abortar una transacción con un mensaje claro."""


def error(texto, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detalle': texto}, status=codigo)


def denegado():
    return error('No puede realizar esta acción en el estado actual.', status.HTTP_403_FORBIDDEN)


def a_decimal(valor, decimales='0.001'):
    try:
        d = Decimal(str(valor))
    except InvalidOperation:
        raise ValueError('número no válido')
    if not d.is_finite():
        raise ValueError('número no válido')
    return d.quantize(Decimal(decimales))


def entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


class SolicitudRecursoViewSet(viewsets.ViewSet):
    permission_classes = [PermisoRecursos]

    def _qs(self, request):
        qs = (SolicitudRecurso.objects
              .select_related('uo', 'orden', 'orden__inmueble', 'orden__centro_costo', 'almacen',
                              'solicitada_por', 'verificada_por', 'autorizada_por', 'despachada_por')
              .prefetch_related('lineas__material'))
        perfil = request.user.perfil
        return qs if perfil.es_central else qs.filter(uo=perfil.uo)

    def _obtener(self, request, pk):
        return get_object_or_404(self._qs(request), pk=pk)

    def _respuesta(self, request, pk, codigo=status.HTTP_200_OK):
        return Response(salida(self._obtener(request, pk), request.user), status=codigo)

    def list(self, request):
        sols = self._qs(request)
        return Response([salida(s, request.user, detalle=False) for s in sols])

    def retrieve(self, request, pk=None):
        return self._respuesta(request, pk)

    def create(self, request):
        perfil = request.user.perfil
        if perfil.rol not in ROLES_CREAN:
            return error('Solo el Especialista o el Jefe de Brigada piden recursos.', status.HTTP_403_FORBIDDEN)

        orden = Orden.objects.filter(pk=entero(request.data.get('orden')), uo=perfil.uo).first()
        if orden is None:
            return error('Seleccione una orden de trabajo válida.')
        if orden.estado not in (Orden.Estado.REGISTRADA, Orden.Estado.EN_EJECUCION):
            return error('Solo se piden recursos para órdenes abiertas.')
        almacen = Almacen.objects.filter(pk=entero(request.data.get('almacen')), uo=perfil.uo).first()
        if almacen is None:
            return error('Seleccione el almacén al que se solicita.')

        lineas = request.data.get('lineas')
        if not isinstance(lineas, list) or not lineas:
            return error('Agregue al menos un material.')

        preparadas, vistos = [], set()
        for l in lineas:
            if not isinstance(l, dict):
                return error('Líneas no válidas.')
            try:
                cantidad = a_decimal(l.get('cantidad'))
            except ValueError:
                return error('Hay una cantidad que no es un número.')
            if cantidad <= 0:
                return error('Las cantidades deben ser mayores que cero.')
            ex = (Existencia.objects.filter(almacen=almacen, material_id=entero(l.get('material')))
                  .select_related('material').first())
            if ex is None:
                return error('Un material no tiene existencia en ese almacén.')
            if ex.material_id in vistos:
                return error(f'El material {ex.material.codigo_sap} está repetido.')
            vistos.add(ex.material_id)
            if cantidad > ex.cantidad_libre:
                return error(f'{ex.material.codigo_sap}: solo hay {ex.cantidad_libre} disponibles.')
            preparadas.append((ex, cantidad))

        hoy = timezone.localdate()
        with transaction.atomic():
            sol = SolicitudRecurso.objects.create(
                uo=perfil.uo, anio=hoy.year, numero=SolicitudRecurso.siguiente_numero(perfil.uo, hoy.year),
                orden=orden, almacen=almacen, solicitada_por=request.user,
            )
            LineaRecurso.objects.bulk_create([
                LineaRecurso(solicitud=sol, material=ex.material, cantidad=c,
                             precio_unitario=ex.valor_unitario or Decimal('0'))
                for ex, c in preparadas
            ])
        return self._respuesta(request, sol.pk, status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def verificar(self, request, pk=None):
        sol = self._obtener(request, pk)
        if 'verificar' not in acciones_recurso(sol, request.user):
            return denegado()
        if (falta := faltante(sol)):
            return error(falta)
        resumen = resumen_presupuesto(sol.uo, sol.anio)
        if not resumen['configurado']:
            return error('Su UO no tiene presupuesto cargado para este año. '
                         'Pida al administrador que lo registre.')
        if total_estimado(sol) <= resumen['disponible']:
            sol.estado = S.VERIFICADA
            sol.verificada_por = request.user
            sol.fecha_verificacion = timezone.now()
        else:
            sol.estado = S.PENDIENTE_SOBREGIRO
        sol.save()
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def autorizar(self, request, pk=None):
        sol = self._obtener(request, pk)
        if 'autorizar' not in acciones_recurso(sol, request.user):
            return denegado()
        if (falta := faltante(sol)):
            return error(falta)
        if total_estimado(sol) > resumen_presupuesto(sol.uo, sol.anio)['disponible']:
            return error('El presupuesto disponible ya no alcanza para esta solicitud.')
        sol.estado = S.AUTORIZADA
        sol.autorizada_por = request.user
        sol.fecha_autorizacion = timezone.now()
        sol.save()
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        sol = self._obtener(request, pk)
        if 'rechazar' not in acciones_recurso(sol, request.user):
            return denegado()
        motivo = str(request.data.get('motivo', '')).strip()
        if not motivo:
            return error('Indique el motivo del rechazo.')
        sol.estado = S.RECHAZADA
        sol.motivo = motivo
        sol.save()
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        sol = self._obtener(request, pk)
        if 'cancelar' not in acciones_recurso(sol, request.user):
            return denegado()
        sol.estado = S.CANCELADA
        sol.motivo = str(request.data.get('motivo', '')).strip()
        sol.save()
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def despachar(self, request, pk=None):
        sol = self._obtener(request, pk)
        if 'despachar' not in acciones_recurso(sol, request.user):
            return denegado()
        vale = str(request.data.get('vale_numero', '')).strip()
        if not vale:
            return error('Indique el número del vale de salida.')

        # Cantidades realmente despachadas (si no se envían, se despacha todo lo autorizado)
        pedidas = {}
        try:
            for x in request.data.get('lineas') or []:
                pedidas[int(x['id'])] = a_decimal(x['cantidad_despachada'])
        except (KeyError, TypeError, ValueError):
            return error('Las cantidades despachadas no son válidas.')

        try:
            with transaction.atomic():
                total_salido = Decimal('0')
                for l in sol.lineas.select_related('material'):
                    cant = pedidas.get(l.id, l.cantidad)
                    if cant < 0 or cant > l.cantidad:
                        raise Fallo(f'{l.material.codigo_sap}: la cantidad debe estar entre 0 y {l.cantidad}.')
                    if cant > 0:
                        ex = (Existencia.objects.select_for_update()
                              .filter(almacen=sol.almacen, material=l.material).first())
                        if ex is None or ex.cantidad_libre < cant:
                            hay = ex.cantidad_libre if ex else 0
                            raise Fallo(f'{l.material.codigo_sap}: en el almacén solo hay {hay}.')
                        ex.cantidad_libre -= cant
                        ex.save()
                        l.precio_unitario = ex.valor_unitario or l.precio_unitario
                    l.cantidad_despachada = cant
                    l.save()
                    total_salido += cant
                if total_salido <= 0:
                    raise Fallo('No se despachó ninguna cantidad.')
                sol.estado = S.DESPACHADA
                sol.vale_numero = vale
                sol.despachada_por = request.user
                sol.fecha_despacho = timezone.now()
                sol.save()
        except Fallo as e:
            return error(str(e))
        return self._respuesta(request, pk)


class SobregiroViewSet(viewsets.ViewSet):
    permission_classes = [PermisoPresupuesto]

    def list(self, request):
        qs = Sobregiro.objects.select_related('uo', 'solicitado_por', 'resuelto_por')
        perfil = request.user.perfil
        if not perfil.es_central:
            qs = qs.filter(uo=perfil.uo)
        return Response([salida_sobregiro(s) for s in qs])

    def create(self, request):
        perfil = request.user.perfil
        if perfil.rol != R.DIRECTOR_UO.value:
            return error('Solo el Director de la UO solicita sobregiros.', status.HTTP_403_FORBIDDEN)
        try:
            monto = a_decimal(request.data.get('monto_solicitado'), '0.01')
        except ValueError:
            return error('El monto solicitado no es un número.')
        if monto <= 0:
            return error('El monto debe ser mayor que cero.')
        fundamentacion = str(request.data.get('fundamentacion', '')).strip()
        if not fundamentacion:
            return error('Escriba la fundamentación del sobregiro.')

        anio = timezone.localdate().year
        if Sobregiro.objects.filter(uo=perfil.uo, anio=anio, estado=Sobregiro.Estado.SOLICITADO).exists():
            return error('Ya hay un sobregiro pendiente de respuesta para este año.')
        r = resumen_presupuesto(perfil.uo, anio)
        s = Sobregiro.objects.create(
            uo=perfil.uo, anio=anio, financiamiento_asignado=r['asignado'], real_gastado=r['gastado'],
            monto_solicitado=monto, fundamentacion=fundamentacion, solicitado_por=request.user,
        )
        return Response(salida_sobregiro(s), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        if request.user.perfil.rol != R.CENTRAL.value:
            return error('Solo el nivel central resuelve los sobregiros.', status.HTTP_403_FORBIDDEN)
        s = get_object_or_404(Sobregiro, pk=pk)
        if s.estado != Sobregiro.Estado.SOLICITADO:
            return error('Este sobregiro ya fue resuelto.')
        aprobar = request.data.get('aprobar') in (True, 'true', 'True', 1, '1')
        respuesta = str(request.data.get('respuesta', '')).strip()
        if aprobar:
            try:
                monto = a_decimal(request.data.get('monto_aprobado', s.monto_solicitado), '0.01')
            except ValueError:
                return error('El monto aprobado no es un número.')
            if monto <= 0:
                return error('El monto aprobado debe ser mayor que cero.')
            s.estado, s.monto_aprobado = Sobregiro.Estado.APROBADO, monto
        else:
            if not respuesta:
                return error('Indique el motivo del rechazo.')
            s.estado = Sobregiro.Estado.RECHAZADO
        s.respuesta = respuesta
        s.resuelto_por = request.user
        s.resuelto = timezone.now()
        s.save()
        return Response(salida_sobregiro(s))


class PresupuestoView(APIView):
    """GET /api/presupuesto/?anio=2026 - resumen de la UO (o de todas, para el nivel central)."""
    permission_classes = [PermisoPresupuesto]

    def get(self, request):
        try:
            anio = int(request.query_params.get('anio') or timezone.localdate().year)
        except ValueError:
            anio = timezone.localdate().year
        perfil = request.user.perfil
        uos = UnidadOrganizativa.objects.filter(activa=True) if perfil.es_central else [perfil.uo]
        return Response([resumen_presupuesto(uo, anio) for uo in uos])


class ExistenciasView(APIView):
    """GET /api/existencias/?almacen=ID&q=texto - máximo 40 resultados."""
    permission_classes = [PermisoRecursos]

    def get(self, request):
        perfil = request.user.perfil
        qs = Existencia.objects.select_related('material', 'almacen').filter(cantidad_libre__gt=0)
        if not perfil.es_central:
            qs = qs.filter(almacen__uo=perfil.uo)
        almacen = entero(request.query_params.get('almacen'))
        if almacen:
            qs = qs.filter(almacen_id=almacen)
        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(material__codigo_sap__icontains=q) | Q(material__descripcion__icontains=q))
        return Response([
            {'id': e.id, 'material': e.material_id, 'codigo_sap': e.material.codigo_sap,
             'descripcion': e.material.descripcion, 'um': e.material.unidad_medida,
             'cantidad_libre': e.cantidad_libre, 'valor_unitario': e.valor_unitario,
             'almacen': e.almacen.codigo}
            for e in qs.order_by('material__descripcion')[:40]
        ])


class AlmacenViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [PermisoRecursos]
    serializer_class = AlmacenSerializer

    def get_queryset(self):
        perfil = self.request.user.perfil
        qs = Almacen.objects.select_related('uo')
        return qs if perfil.es_central else qs.filter(uo=perfil.uo)
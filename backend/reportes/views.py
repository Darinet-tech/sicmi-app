from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Perfil, UnidadOrganizativa
from . import calculos
from .models import Certificacion, CertificacionFirma, HistorialCertificacion
from .permissions import PermisoReportes
from .reglas import acciones_permitidas
from .salidas import salida_cert

R = Perfil.Rol
C = Certificacion.Estado


def error(texto, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detalle': texto}, status=codigo)


def prohibido(texto='No tiene permiso para esta acción.'):
    return error(texto, status.HTTP_403_FORBIDDEN)


def entero(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def resolver_uos(request):
    """Las UO de las que se calculan los datos. El nivel central puede elegir una con ?uo=ID."""
    perfil = request.user.perfil
    if not perfil.es_central:
        return [perfil.uo_id], perfil.uo
    uo_id = entero(request.query_params.get('uo'))
    if uo_id:
        uo = UnidadOrganizativa.objects.filter(pk=uo_id).first()
        return ([uo.id], uo) if uo else (None, None)
    return list(UnidadOrganizativa.objects.filter(activa=True).values_list('id', flat=True)), None


class SeriesView(APIView):
    """GET /api/reportes/series/?periodo=semana|mes|anio&anio=2026&uo=ID"""
    permission_classes = [PermisoReportes]

    def get(self, request):
        uos, _ = resolver_uos(request)
        if uos is None:
            return error('Unidad organizativa no válida.')
        hoy = timezone.localdate()
        periodo = request.query_params.get('periodo', 'mes')
        if periodo not in ('semana', 'mes', 'anio'):
            return error('Período no válido.')
        anio = entero(request.query_params.get('anio')) or hoy.year
        if not 2000 <= anio <= 2100:
            return error('Año no válido.')
        return Response(calculos.series(uos, periodo, anio, hoy))


class IndicadoresView(APIView):
    """GET /api/reportes/indicadores/?anio=2026&mes=3&uo=ID"""
    permission_classes = [PermisoReportes]

    def get(self, request):
        uos, _ = resolver_uos(request)
        if uos is None:
            return error('Unidad organizativa no válida.')
        hoy = timezone.localdate()
        anio = entero(request.query_params.get('anio')) or hoy.year
        mes = entero(request.query_params.get('mes')) or hoy.month
        if not 2000 <= anio <= 2100 or not 1 <= mes <= 12:
            return error('Año o mes no válido.')
        return Response(calculos.indicadores(uos, anio, mes))


class UnidadesView(APIView):
    """GET /api/reportes/unidades/ - lista de UO para el selector del nivel central."""
    permission_classes = [PermisoReportes]

    def get(self, request):
        if not request.user.perfil.es_central:
            return Response([])
        return Response([{'id': u.id, 'acronimo': u.acronimo, 'nombre': u.nombre}
                         for u in UnidadOrganizativa.objects.filter(activa=True)])


class CertificacionViewSet(viewsets.ViewSet):
    permission_classes = [PermisoReportes]

    def _qs(self, request):
        qs = Certificacion.objects.select_related('uo').prefetch_related('firmas__usuario', 'historial__usuario')
        perfil = request.user.perfil
        return qs if perfil.es_central else qs.filter(uo=perfil.uo)

    def _obtener(self, request, pk):
        return get_object_or_404(self._qs(request), pk=pk)

    def _respuesta(self, request, pk, codigo=status.HTTP_200_OK):
        return Response(salida_cert(self._obtener(request, pk), request.user), status=codigo)

    def _nota(self, cert, request, texto):
        HistorialCertificacion.objects.create(certificacion=cert, usuario=request.user, comentario=texto)

    def list(self, request):
        return Response([salida_cert(c, request.user, detalle=False) for c in self._qs(request)])

    def retrieve(self, request, pk=None):
        return self._respuesta(request, pk)

    def create(self, request):
        perfil = request.user.perfil
        if perfil.rol != R.ESPECIALISTA.value:
            return prohibido('Solo el Especialista elabora la certificación mensual.')
        hoy = timezone.localdate()
        anio, mes = entero(request.data.get('anio')), entero(request.data.get('mes'))
        if anio is None or mes is None or not 1 <= mes <= 12:
            return error('Indique el mes y el año.')
        if (anio, mes) > (hoy.year, hoy.month):
            return error('No se puede certificar un mes que todavía no ha comenzado.')
        if anio < hoy.year - 5:
            return error('Año no válido.')
        if Certificacion.objects.filter(uo=perfil.uo, anio=anio, mes=mes).exists():
            return error('Ya existe la certificación de ese mes para su UO.')
        with transaction.atomic():
            c = Certificacion.objects.create(uo=perfil.uo, anio=anio, mes=mes,
                                             datos=calculos.calcular_snapshot(perfil.uo, anio, mes))
            self._nota(c, request, 'Certificación generada con los datos del sistema')
        return self._respuesta(request, c.pk, status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def actualizar(self, request, pk=None):
        c = self._obtener(request, pk)
        if 'actualizar' not in acciones_permitidas(c, request.user):
            return prohibido()
        c.datos = calculos.calcular_snapshot(c.uo, c.anio, c.mes)
        c.save()
        self._nota(c, request, 'Datos actualizados desde el sistema')
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def incidencias(self, request, pk=None):
        c = self._obtener(request, pk)
        if 'incidencias' not in acciones_permitidas(c, request.user):
            return prohibido()
        texto = request.data.get('incidencias')
        if not isinstance(texto, dict):
            return error('Las incidencias no son válidas.')
        validas = {f['clave'] for f in (c.datos or {}).get('filas', [])}
        c.incidencias = {k: str(v).strip()[:300] for k, v in texto.items() if k in validas and str(v).strip()}
        c.save()
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        c = self._obtener(request, pk)
        if 'enviar' not in acciones_permitidas(c, request.user):
            return prohibido()
        with transaction.atomic():
            CertificacionFirma.objects.create(certificacion=c, rol=request.user.perfil.rol, usuario=request.user)
            c.estado = C.EN_FIRMAS
            c.motivo_devolucion = ''
            c.save()
            self._nota(c, request, 'Certificación enviada a revisión y firmas')
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def firmar(self, request, pk=None):
        c = self._obtener(request, pk)
        if 'firmar' not in acciones_permitidas(c, request.user):
            return prohibido()
        rol = request.user.perfil.rol
        with transaction.atomic():
            CertificacionFirma.objects.create(certificacion=c, rol=rol, usuario=request.user)
            if rol == R.JEFE_LOGISTICA.value:
                c.estado = C.APROBADA
                c.save()
                texto = 'Certificación aprobada: lista para enviar a Inmobiliaria'
            else:
                texto = f'Firma registrada: {request.user.perfil.get_rol_display()}'
            self._nota(c, request, texto)
        return self._respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        c = self._obtener(request, pk)
        if 'devolver' not in acciones_permitidas(c, request.user):
            return prohibido()
        motivo = str(request.data.get('motivo', '')).strip()
        if not motivo:
            return error('Indique el motivo de la devolución.')
        with transaction.atomic():
            c.firmas.all().delete()
            c.estado = C.BORRADOR
            c.motivo_devolucion = motivo
            c.save()
            self._nota(c, request, f'Certificación devuelta por {request.user.perfil.get_rol_display()}: {motivo}')
        return self._respuesta(request, pk)
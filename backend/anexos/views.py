from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Perfil
from ordenes.models import Orden
from plan.models import AccionPlan, PlanAnual
from plan.permissions import PermisoPlan
from recursos.models import SolicitudRecurso, Sobregiro
from recursos.permissions import PermisoPresupuesto, PermisoRecursos
from solicitudes.models import Solicitud
from solicitudes.permissions import TienePerfil
from . import documentos
from .render import a_excel, a_pdf


def entregar(doc, request):
    formato = request.query_params.get('formato', 'pdf')
    if formato == 'xlsx':
        datos, mime, ext = a_excel(doc), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx'
    elif formato == 'pdf':
        datos, mime, ext = a_pdf(doc), 'application/pdf', 'pdf'
    else:
        return Response({'detalle': 'Formato no válido: use pdf o xlsx.'}, status=status.HTTP_400_BAD_REQUEST)
    r = HttpResponse(datos, content_type=mime)
    r['Content-Disposition'] = f'attachment; filename="{doc.archivo}.{ext}"'
    return r


def de_su_uo(qs, perfil, campo='uo'):
    return qs if perfil.es_central else qs.filter(**{campo: perfil.uo})


class AnexoSolicitud(APIView):
    permission_classes = [TienePerfil]

    def get(self, request, pk):
        perfil = request.user.perfil
        qs = de_su_uo(Solicitud.objects.select_related(
            'uo', 'inmueble', 'centro_costo', 'area_solicitante', 'local', 'afectacion', 'solicitante'), perfil)
        if perfil.rol == Perfil.Rol.CLIENTE:
            qs = qs.filter(solicitante=request.user)
        return entregar(documentos.anexo1(get_object_or_404(qs, pk=pk)), request)


class AnexoRegistroOrdenes(APIView):
    permission_classes = [TienePerfil]

    def get(self, request):
        perfil = request.user.perfil
        if perfil.rol == Perfil.Rol.CLIENTE:
            return Response({'detalle': 'Su rol no tiene acceso a este documento.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            anio = int(request.query_params.get('anio') or timezone.localdate().year)
        except ValueError:
            anio = timezone.localdate().year
        qs = (Orden.objects.filter(anio=anio, numero__isnull=False)
              .select_related('uo', 'inmueble', 'centro_costo')
              .prefetch_related('solicitudes_recursos', 'historial'))
        ordenes = sorted(de_su_uo(qs, perfil), key=lambda o: (o.uo.acronimo, o.numero))
        return entregar(documentos.anexo2(perfil.uo, anio, ordenes), request)


class AnexoRecursos(APIView):
    permission_classes = [PermisoRecursos]

    def get(self, request, pk):
        perfil = request.user.perfil
        qs = de_su_uo(SolicitudRecurso.objects.select_related(
            'uo', 'orden', 'orden__inmueble', 'orden__centro_costo', 'orden__area_solicitante', 'almacen',
            'solicitada_por', 'autorizada_por', 'despachada_por'
        ).prefetch_related('lineas__material', 'lineas__sobrantes__registrado_por'), perfil)
        sol = get_object_or_404(qs, pk=pk)
        tipo = request.query_params.get('tipo', 'salida')
        if tipo not in ('salida', 'devolucion'):
            return Response({'detalle': 'Tipo no válido.'}, status=status.HTTP_400_BAD_REQUEST)
        if tipo == 'devolucion' and sol.estado != SolicitudRecurso.Estado.DESPACHADA:
            return Response({'detalle': 'La devolución solo aplica a solicitudes ya despachadas.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return entregar(documentos.anexo3(sol, tipo), request)


class _AnexoSobregiro(APIView):
    permission_classes = [PermisoPresupuesto]
    constructor = None
    solo_aprobado = False

    def get(self, request, pk):
        qs = de_su_uo(Sobregiro.objects.select_related('uo', 'solicitado_por', 'resuelto_por'), request.user.perfil)
        s = get_object_or_404(qs, pk=pk)
        if self.solo_aprobado and s.estado != Sobregiro.Estado.APROBADO:
            return Response({'detalle': 'El Anexo 5 solo existe para sobregiros aprobados.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return entregar(type(self).constructor(s), request)


class AnexoSobregiro(_AnexoSobregiro):
    constructor = staticmethod(documentos.anexo4)


class AnexoAprobacion(_AnexoSobregiro):
    constructor = staticmethod(documentos.anexo5)
    solo_aprobado = True


class AnexoOrden(APIView):
    permission_classes = [TienePerfil]

    def get(self, request, pk):
        perfil = request.user.perfil
        qs = de_su_uo(Orden.objects.select_related(
            'uo', 'inmueble', 'centro_costo', 'area_solicitante', 'local', 'cliente', 'vehiculo'
        ).prefetch_related('brigadas__brigada', 'participantes__trabajador', 'firmas__usuario'), perfil)
        if perfil.rol == Perfil.Rol.CLIENTE:
            qs = qs.filter(cliente=request.user).exclude(estado=Orden.Estado.EN_PROCESO)
        return entregar(documentos.anexo6(get_object_or_404(qs, pk=pk)), request)


# ---------- Plan anual preventivo (Anexos 7, 8 y 9) ----------
class AnexoPlan(APIView):
    permission_classes = [PermisoPlan]

    def get(self, request, pk):
        qs = de_su_uo(PlanAnual.objects.select_related('uo'), request.user.perfil)
        return entregar(documentos.anexo9(get_object_or_404(qs, pk=pk)), request)


class _AnexoObra(APIView):
    permission_classes = [PermisoPlan]
    relacion = ''   # 'tarea_tecnica' o 'croquis'
    faltante = ''
    constructor = None

    def get(self, request, pk):
        qs = de_su_uo(AccionPlan.objects.select_related('plan__uo', 'inmueble', 'grupo'),
                      request.user.perfil, campo='plan__uo')
        accion = get_object_or_404(qs, pk=pk)
        if not hasattr(accion, self.relacion):
            return Response({'detalle': self.faltante}, status=status.HTTP_404_NOT_FOUND)
        # El Anexo 7 se construye desde la obra; el Anexo 8, desde el croquis
        base = getattr(accion, self.relacion) if self.relacion == 'croquis' else accion
        return entregar(type(self).constructor(base), request)


class AnexoTareaTecnica(_AnexoObra):
    relacion = 'tarea_tecnica'
    faltante = 'Esta obra todavía no tiene Tarea técnica.'
    constructor = staticmethod(documentos.anexo7)


class AnexoCroquis(_AnexoObra):
    relacion = 'croquis'
    faltante = 'Esta obra todavía no tiene croquis.'
    constructor = staticmethod(documentos.anexo8)

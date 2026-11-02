from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Perfil
from catalogos.models import AreaSolicitante, CentroCosto, GrupoGenerico, Inmueble, Local
from ordenes.models import HistorialOrden, Orden
from ordenes.servicios import agregar_brigada_a_orden
from personal.models import Brigada
from transporte.models import EstadoVehiculo, Vehiculo
from transporte.utils import estado_vehiculo
from .models import AccionPlan, Croquis, HistorialPlan, PlanAnual, PlanFirma, TareaTecnica
from .permissions import PermisoPlan
from .reglas import acciones_permitidas
from .serializers import salida_plan, salida_croquis, salida_tt

R = Perfil.Rol
P = PlanAnual.Estado


def error(texto, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detalle': texto}, status=codigo)


def prohibido(texto='No tiene permiso para esta acción.'):
    return error(texto, status.HTTP_403_FORBIDDEN)


def entero(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def es_especialista(request):
    return request.user.perfil.rol == R.ESPECIALISTA.value


def qs_planes(request):
    qs = (PlanAnual.objects.select_related('uo', 'elaborado_por')
          .prefetch_related('acciones__inmueble', 'acciones__grupo', 'acciones__ordenes',
                            'acciones__tarea_tecnica', 'acciones__croquis',
                            'firmas__usuario', 'historial__usuario'))
    perfil = request.user.perfil
    return qs if perfil.es_central else qs.filter(uo=perfil.uo)


def plan_respuesta(request, plan_id, codigo=status.HTTP_200_OK):
    plan = get_object_or_404(qs_planes(request), pk=plan_id)
    return Response(salida_plan(plan, request.user), status=codigo)


def validar_accion(data, uo, actual=None):
    """Valida y normaliza los datos de una obra. Devuelve (datos, mensaje_de_error)."""
    d = {}
    nueva = actual is None
    if 'inmueble' in data or nueva:
        inm = Inmueble.objects.filter(pk=entero(data.get('inmueble')), uo=uo, activo=True).first()
        if inm is None:
            return None, 'Seleccione un inmueble de su UO.'
        d['inmueble'] = inm
    if 'grupo' in data or nueva:
        g = GrupoGenerico.objects.filter(pk=entero(data.get('grupo'))).first()
        if g is None:
            return None, 'Seleccione el grupo genérico de la obra.'
        d['grupo'] = g
    if 'descripcion' in data:
        d['descripcion'] = str(data.get('descripcion') or '').strip()
    if 'via' in data or nueva:
        via = data.get('via', AccionPlan.Via.PROPIOS)
        if via not in AccionPlan.Via.values:
            return None, 'Vía de ejecución no válida.'
        d['via'] = via
    if 'prioridad' in data or nueva:
        pr = entero(data.get('prioridad', 4))
        if pr not in (1, 2, 3, 4):
            return None, 'Prioridad no válida.'
        d['prioridad'] = pr
    if 'es_compleja' in data:
        d['es_compleja'] = data.get('es_compleja') in (True, 'true', 'True', 1, '1')
    if 'valor_estimado' in data:
        try:
            v = Decimal(str(data.get('valor_estimado') or 0)).quantize(Decimal('0.001'))
        except InvalidOperation:
            return None, 'El valor estimado no es un número.'
        if v < 0:
            return None, 'El valor estimado no puede ser negativo.'
        d['valor_estimado'] = v
    if 'programacion' in data:
        prog = data.get('programacion')
        if not isinstance(prog, dict):
            return None, 'La programación no es válida.'
        limpia = {}
        for k, n in prog.items():
            mes = entero(k)
            cant = 0 if n in ('', None) else entero(n)
            if mes is None or not 1 <= mes <= 12 or cant is None or not 0 <= cant <= 99:
                return None, 'La programación no es válida: use cantidades de 0 a 99 por mes.'
            if cant:
                limpia[str(mes)] = cant
        d['programacion'] = limpia
    return d, None


class PlanViewSet(viewsets.ViewSet):
    permission_classes = [PermisoPlan]

    def list(self, request):
        return Response([salida_plan(p, request.user, detalle=False) for p in qs_planes(request)])

    def retrieve(self, request, pk=None):
        return plan_respuesta(request, pk)

    def create(self, request):
        if not es_especialista(request):
            return prohibido('Solo el Especialista elabora el plan.')
        hoy = timezone.localdate()
        anio = entero(request.data.get('anio'))
        if anio is None or not hoy.year - 1 <= anio <= hoy.year + 2:
            return error(f'Indique un año entre {hoy.year - 1} y {hoy.year + 2}.')
        uo = request.user.perfil.uo
        if PlanAnual.objects.filter(uo=uo, anio=anio).exists():
            return error(f'Ya existe el plan de {anio} para su UO.')
        with transaction.atomic():
            plan = PlanAnual.objects.create(uo=uo, anio=anio, elaborado_por=request.user)
            HistorialPlan.objects.create(plan=plan, usuario=request.user, comentario='Plan creado')
        return plan_respuesta(request, plan.pk, status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        plan = get_object_or_404(qs_planes(request), pk=pk)
        if 'enviar' not in acciones_permitidas(plan, request.user):
            return prohibido()
        propias = [a for a in plan.acciones.all() if a.via == AccionPlan.Via.PROPIOS]
        if not propias:
            return error('Agregue al menos una obra por medios propios.')
        for a in propias:
            ref = f'«{a.grupo.nombre}» en {a.inmueble.denominacion}'
            if a.cantidad == 0:
                return error(f'{ref}: indique en qué meses se ejecutará.')
            if a.valor_estimado <= 0:
                return error(f'{ref}: indique el valor estimado (MCUP).')
        with transaction.atomic():
            PlanFirma.objects.create(plan=plan, rol=request.user.perfil.rol, usuario=request.user)
            plan.estado = P.EN_FIRMAS
            plan.motivo_devolucion = ''
            plan.save()
            HistorialPlan.objects.create(plan=plan, usuario=request.user,
                                         comentario='Plan enviado a revisión y firmas')
        return plan_respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def firmar(self, request, pk=None):
        plan = get_object_or_404(qs_planes(request), pk=pk)
        if 'firmar' not in acciones_permitidas(plan, request.user):
            return prohibido()
        rol = request.user.perfil.rol
        with transaction.atomic():
            PlanFirma.objects.create(plan=plan, rol=rol, usuario=request.user)
            if rol == R.DIRECTOR_UO.value:
                plan.estado = P.APROBADO
                plan.save()
                texto = 'Plan aprobado por el Director de la UO'
            else:
                texto = f'Firma registrada: {request.user.perfil.get_rol_display()}'
            HistorialPlan.objects.create(plan=plan, usuario=request.user, comentario=texto)
        return plan_respuesta(request, pk)

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        plan = get_object_or_404(qs_planes(request), pk=pk)
        if 'devolver' not in acciones_permitidas(plan, request.user):
            return prohibido()
        motivo = str(request.data.get('motivo', '')).strip()
        if not motivo:
            return error('Indique el motivo de la devolución.')
        with transaction.atomic():
            plan.firmas.all().delete()
            plan.estado = P.BORRADOR
            plan.motivo_devolucion = motivo
            plan.save()
            HistorialPlan.objects.create(
                plan=plan, usuario=request.user,
                comentario=f'Plan devuelto por {request.user.perfil.get_rol_display()}: {motivo}')
        return plan_respuesta(request, pk)


class AccionViewSet(viewsets.ViewSet):
    permission_classes = [PermisoPlan]

    def _qs(self, request):
        qs = AccionPlan.objects.select_related('plan', 'plan__uo', 'inmueble', 'grupo')
        perfil = request.user.perfil
        return qs if perfil.es_central else qs.filter(plan__uo=perfil.uo)

    def _obtener(self, request, pk):
        return get_object_or_404(self._qs(request), pk=pk)

    def _puede_tecnica(self, request, a):
        return es_especialista(request) and a.plan.estado in (P.BORRADOR, P.APROBADO)

    def retrieve(self, request, pk=None):
        a = self._obtener(request, pk)
        return Response({
            'id': a.id, 'plan': a.plan_id, 'anio': a.plan.anio, 'estado_plan': a.plan.estado,
            'inmueble': a.inmueble_id, 'inmueble_nombre': a.inmueble.denominacion,
            'grupo_nombre': f'{a.grupo.numero}. {a.grupo.nombre}', 'descripcion': a.descripcion,
            'es_compleja': a.es_compleja, 'via': a.via, 'programacion': a.programacion,
            'puede_editar_tecnica': self._puede_tecnica(request, a),
        })

    def create(self, request):
        if not es_especialista(request):
            return prohibido()
        plan = get_object_or_404(qs_planes(request), pk=entero(request.data.get('plan')))
        if plan.estado != P.BORRADOR:
            return error('El plan ya no se puede modificar: está en revisión o aprobado.')
        datos, err = validar_accion(request.data, plan.uo)
        if err:
            return error(err)
        AccionPlan.objects.create(plan=plan, **datos)
        return plan_respuesta(request, plan.pk, status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        a = self._obtener(request, pk)
        if not es_especialista(request):
            return prohibido()
        if a.plan.estado != P.BORRADOR:
            return error('El plan ya no se puede modificar: está en revisión o aprobado.')
        datos, err = validar_accion(request.data, a.plan.uo, actual=a)
        if err:
            return error(err)
        for k, v in datos.items():
            setattr(a, k, v)
        a.save()
        return plan_respuesta(request, a.plan_id)

    def destroy(self, request, pk=None):
        a = self._obtener(request, pk)
        if not es_especialista(request):
            return prohibido()
        if a.plan.estado != P.BORRADOR:
            return error('El plan ya no se puede modificar: está en revisión o aprobado.')
        plan_id = a.plan_id
        a.delete()
        return plan_respuesta(request, plan_id)

    # ---------- Anexo 7 ----------
    @action(detail=True, methods=['get', 'put'], url_path='tarea-tecnica')
    def tarea_tecnica(self, request, pk=None):
        a = self._obtener(request, pk)
        tt = TareaTecnica.objects.filter(accion=a).first()
        if request.method == 'GET':
            return Response(salida_tt(tt, request.user))
        if not self._puede_tecnica(request, a):
            return prohibido()
        trabajos = request.data.get('trabajos')
        if not isinstance(trabajos, list) or len(trabajos) > 60:
            return error('Los trabajos constructivos no son válidos.')
        limpios = []
        for t in trabajos:
            if not isinstance(t, dict):
                return error('Los trabajos constructivos no son válidos.')
            fila = {k: str(t.get(k) or '').strip()[:200] for k in ('desperfecto', 'trabajo', 'um', 'cantidad')}
            if any(fila.values()):
                if not fila['trabajo']:
                    return error('Cada fila debe indicar el trabajo a realizar.')
                limpios.append(fila)
        if not limpios:
            return error('Agregue al menos un trabajo constructivo.')
        tt, _ = TareaTecnica.objects.update_or_create(accion=a, defaults={
            'descripcion_general': str(request.data.get('descripcion_general') or '').strip()[:4000],
            'trabajos': limpios,
            'elaborado_nombre': str(request.data.get('elaborado_nombre') or '').strip()[:150],
            'elaborado_cargo': str(request.data.get('elaborado_cargo') or '').strip()[:150],
        })
        return Response(salida_tt(tt, request.user))

    # ---------- Anexo 8 ----------
    @action(detail=True, methods=['get', 'post', 'delete'], parser_classes=[MultiPartParser, FormParser])
    def croquis(self, request, pk=None):
        a = self._obtener(request, pk)
        c = Croquis.objects.filter(accion=a).first()
        if request.method == 'GET':
            return Response(salida_croquis(c))
        if not self._puede_tecnica(request, a):
            return prohibido()
        if request.method == 'DELETE':
            if c:
                c.imagen.delete(save=False)
                c.delete()
            return Response(salida_croquis(None))

        archivo = request.FILES.get('imagen')
        if archivo is None and c is None:
            return error('Seleccione la imagen del croquis (JPG o PNG).')
        contenido = None
        if archivo is not None:
            if archivo.size > 8 * 1024 * 1024:
                return error('La imagen no puede pesar más de 8 MB.')
            try:
                img = ImageOps.exif_transpose(Image.open(archivo))
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                    fondo = Image.new('RGB', img.size, 'white')
                    fondo.paste(img, mask=img.getchannel('A'))
                    img = fondo
                else:
                    img = img.convert('RGB')
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                return error('El archivo no es una imagen válida (use JPG o PNG).')
            img.thumbnail((2400, 2400))
            buf = BytesIO()
            img.save(buf, 'JPEG', quality=85)
            contenido = ContentFile(buf.getvalue(), name=f'croquis_{a.id}.jpg')

        datos = {k: str(request.data.get(k, '')).strip()[:150]
                 for k in ('plano_no', 'escala', 'proyecto', 'plano', 'elaborado', 'proyectado', 'aprobado')}
        datos['fecha'] = parse_date(str(request.data.get('fecha', '')))
        with transaction.atomic():
            if c is None:
                c = Croquis(accion=a)
            for k, v in datos.items():
                setattr(c, k, v)
            if contenido is not None:
                if c.imagen:
                    c.imagen.delete(save=False)
                c.imagen.save(contenido.name, contenido, save=False)
            c.save()
        return Response(salida_croquis(c))

    # ---------- Órdenes preventivas ----------
    @action(detail=True, methods=['post'], url_path='generar-orden')
    def generar_orden(self, request, pk=None):
        a = self._obtener(request, pk)
        perfil = request.user.perfil
        if perfil.rol != R.ESPECIALISTA.value:
            return prohibido('Solo el Especialista genera las órdenes del plan.')
        if a.plan.estado != P.APROBADO:
            return error('El plan debe estar aprobado para generar órdenes.')
        if a.via != AccionPlan.Via.PROPIOS:
            return error('Esta obra no se ejecuta por medios propios.')

        mes = entero(request.data.get('mes'))
        programadas = a.programacion.get(str(mes), 0) if mes else 0
        if not programadas:
            return error('Ese mes no está programado para esta obra.')
        hechas = (Orden.objects.filter(accion_plan=a, mes_plan=mes)
                  .exclude(estado=Orden.Estado.CANCELADA).count())
        if hechas >= programadas:
            return error('Ya se generaron todas las órdenes programadas para ese mes.')
        if a.es_compleja and not TareaTecnica.objects.filter(accion=a).exists():
            return error('Es una obra compleja: prepare primero la Tarea técnica (Anexo 7).')

        uo = perfil.uo
        User = get_user_model()
        centro = CentroCosto.objects.filter(pk=entero(request.data.get('centro_costo')), uo=uo).first()
        area = AreaSolicitante.objects.filter(pk=entero(request.data.get('area_solicitante')), uo=uo).first()
        cliente = User.objects.filter(pk=entero(request.data.get('cliente')), is_active=True,
                                      perfil__rol=R.CLIENTE.value, perfil__uo=uo).first()
        if centro is None:
            return error('Seleccione el centro de costo.')
        if area is None:
            return error('Seleccione el área solicitante.')
        if cliente is None:
            return error('Seleccione el cliente (jefe del inmueble) que confirmará el trabajo.')
        local = None
        if request.data.get('local'):
            local = Local.objects.filter(pk=entero(request.data.get('local')), inmueble=a.inmueble, activo=True).first()
            if local is None:
                return error('Local no válido para este inmueble.')

        hoy = timezone.localdate()
        brigada = vehiculo = None
        if request.data.get('brigada'):
            brigada = Brigada.objects.filter(pk=entero(request.data['brigada']), uo=uo, activa=True).first()
            if brigada is None:
                return error('Brigada no válida.')
        if request.data.get('vehiculo'):
            vehiculo = Vehiculo.objects.filter(pk=entero(request.data['vehiculo']), uo=uo, activo=True).first()
            if vehiculo is None:
                return error('Vehículo no válido.')
            if estado_vehiculo(vehiculo, hoy) != EstadoVehiculo.Estado.DISPONIBLE:
                return error(f'El vehículo {vehiculo.chapa} no está disponible hoy.')

        with transaction.atomic():
            orden = Orden.objects.create(
                uo=uo, anio=hoy.year, numero=None, estado=Orden.Estado.EN_PROCESO,
                tipo=Orden.Tipo.PREVENTIVO, solicitud=None,
                inmueble=a.inmueble, centro_costo=centro, area_solicitante=area, local=local, cliente=cliente,
                afectacion=a.grupo.nombre,
                descripcion_solicitud=a.descripcion or f'Mantenimiento preventivo: {a.grupo.nombre}',
                inspeccion_por=request.user.get_full_name() or request.user.username,
                vehiculo=vehiculo, fecha_solicitud=hoy, accion_plan=a, mes_plan=mes,
            )
            HistorialOrden.objects.create(
                orden=orden, estado_nuevo=orden.estado, usuario=request.user,
                comentario=f'Orden preventiva creada en proceso desde el Plan Anual {a.plan.anio}',
            )
            avisos = agregar_brigada_a_orden(orden, brigada, request.user) if brigada else []
        return Response({'id': orden.id, 'codigo': orden.codigo, 'avisos': avisos},
                        status=status.HTTP_201_CREATED)


class ClientesView(APIView):
    """GET /api/plan-clientes/ - usuarios Cliente de la UO (jefes de inmuebles) para las órdenes preventivas."""
    permission_classes = [PermisoPlan]

    def get(self, request):
        perfil = request.user.perfil
        if perfil.rol != R.ESPECIALISTA.value:
            return prohibido()
        User = get_user_model()
        qs = User.objects.filter(is_active=True, perfil__rol=R.CLIENTE.value,
                                 perfil__uo=perfil.uo).select_related('perfil')
        return Response([{'id': u.id, 'nombre': u.get_full_name() or u.username, 'cargo': u.perfil.cargo}
                         for u in qs])
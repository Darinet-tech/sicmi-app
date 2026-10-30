from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Perfil
from personal.models import Trabajador, Brigada, EstadoDiario
from personal.utils import estado_trabajador
from solicitudes.models import Solicitud, HistorialEstado
from solicitudes.permissions import TienePerfil
from transporte.models import Vehiculo, EstadoVehiculo
from transporte.utils import estado_vehiculo
from .models import Orden, ParticipanteOrden, Firma, HistorialOrden
from .reglas import acciones_permitidas
from .serializers import OrdenSerializer, OrdenEdicionSerializer
from .servicios import agregar_brigada_a_orden, cerrar_brigada

E = Orden.Estado


def error(texto, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detalle': texto}, status=codigo)


class OrdenViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrdenSerializer
    permission_classes = [TienePerfil]

    def get_queryset(self):
        qs = (Orden.objects
              .select_related('uo', 'inmueble', 'area_solicitante', 'local', 'centro_costo', 'cliente', 'vehiculo')
              .prefetch_related('brigadas__brigada', 'participantes__trabajador',
                                'firmas__usuario', 'historial__usuario'))
        perfil = self.request.user.perfil
        if perfil.es_central:
            return qs
        qs = qs.filter(uo=perfil.uo)
        if perfil.rol == Perfil.Rol.CLIENTE:
            qs = qs.filter(cliente=self.request.user)  # el cliente solo ve las suyas
        return qs

    # ---------- ayudas ----------
    def salida(self, orden, avisos=None):
        orden = self.get_queryset().get(pk=orden.pk)  # recargar con datos frescos
        datos = OrdenSerializer(orden, context=self.get_serializer_context()).data
        if avisos:
            datos['avisos'] = avisos
        return Response(datos)

    def _permitido(self, orden, accion):
        if accion in acciones_permitidas(orden, self.request.user):
            return None
        return error('No puede realizar esta acción en el estado actual de la orden.', status.HTTP_403_FORBIDDEN)

    def _cambiar(self, orden, nuevo, comentario=''):
        with transaction.atomic():
            anterior = orden.estado
            orden.estado = nuevo
            orden.save()
            HistorialOrden.objects.create(
                orden=orden, estado_anterior=anterior, estado_nuevo=nuevo,
                usuario=self.request.user, comentario=comentario,
            )

    def _nota(self, orden, comentario):
        HistorialOrden.objects.create(
            orden=orden, estado_anterior=orden.estado, estado_nuevo=orden.estado,
            usuario=self.request.user, comentario=comentario,
        )

    # ---------- datos de la orden ----------
    @action(detail=True, methods=['patch'])
    def editar(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'editar')):
            return e
        s = OrdenEdicionSerializer(orden, data=request.data, partial=True, context=self.get_serializer_context())
        s.is_valid(raise_exception=True)
        s.save()
        return self.salida(orden)

    # ---------- ciclo de vida ----------
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'iniciar')):
            return e
        if not orden.participantes.filter(hasta__isnull=True).exists():
            return error('Agregue al menos un participante antes de iniciar la ejecución.')
        self._cambiar(orden, E.EN_EJECUCION, 'Ejecución iniciada')
        return self.salida(orden)

    @action(detail=True, methods=['post'])
    def entregar(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'entregar')):
            return e
        if not orden.descripcion_trabajos.strip():
            return error('Describa los trabajos realizados antes de entregar la orden.')
        self._cambiar(orden, E.ENTREGADA, 'Trabajo entregado al cliente')
        return self.salida(orden)

    @action(detail=True, methods=['post'])
    def conformidad(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'conformidad')):
            return e
        conforme = request.data.get('conforme') in (True, 'true', 'True', 1, '1')
        comentario = str(request.data.get('comentario', '')).strip()
        if conforme:
            with transaction.atomic():
                Firma.objects.create(orden=orden, rol=Perfil.Rol.CLIENTE.value, usuario=request.user)
                self._cambiar(orden, E.CONFORME, 'El cliente está conforme con el trabajo')
        else:
            if not comentario:
                return error('Indique el motivo de su no conformidad.')
            self._cambiar(orden, E.EN_EJECUCION, f'Cliente no conforme. Se rectificará: {comentario}')
        return self.salida(orden)

    @action(detail=True, methods=['post'])
    def firmar(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'firmar')):
            return e
        rol = request.user.perfil.rol
        with transaction.atomic():
            Firma.objects.create(orden=orden, rol=rol, usuario=request.user)
            if rol == Perfil.Rol.ESPECIALISTA:
                # Última firma: se cierra la orden y, con ella, la solicitud
                hoy = timezone.localdate()
                orden.participantes.filter(hasta__isnull=True).update(hasta=hoy)
                orden.brigadas.filter(hasta__isnull=True).update(hasta=hoy)
                orden.fecha_cierre = hoy
                self._cambiar(orden, E.CERRADA, 'Orden cerrada con la firma del Especialista')
                if orden.solicitud_id:
                    sol = orden.solicitud
                    anterior = sol.estado
                    sol.estado = Solicitud.Estado.CERRADA
                    sol.save()
                    HistorialEstado.objects.create(
                        solicitud=sol, estado_anterior=anterior, estado_nuevo=sol.estado,
                        usuario=request.user, comentario=f'Orden {orden.codigo} cerrada',
                    )
            else:
                self._nota(orden, f'Firma registrada: {request.user.perfil.get_rol_display()}')
        return self.salida(orden)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'cancelar')):
            return e
        motivo = str(request.data.get('comentario', '')).strip()
        if not motivo:
            return error('Indique el motivo de la cancelación.')
        with transaction.atomic():
            self._cambiar(orden, E.CANCELADA, f'Orden cancelada: {motivo}')
            if orden.solicitud_id:
                sol = orden.solicitud
                anterior = sol.estado
                sol.estado = Solicitud.Estado.CANCELADA
                sol.save()
                HistorialEstado.objects.create(
                    solicitud=sol, estado_anterior=anterior, estado_nuevo=sol.estado,
                    usuario=request.user, comentario=f'Orden {orden.codigo} cancelada: {motivo}',
                )
        return self.salida(orden)

    # ---------- participantes y brigadas ----------
    @action(detail=True, methods=['post'])
    def agregar_participante(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'editar')):
            return e
        try:
            t = Trabajador.objects.get(pk=request.data.get('trabajador'), uo=orden.uo, activo=True)
        except (Trabajador.DoesNotExist, ValueError, TypeError):
            return error('Trabajador no válido.')
        if orden.participantes.filter(trabajador=t, hasta__isnull=True).exists():
            return error(f'{t.nombre} ya participa en esta orden.')
        hoy = timezone.localdate()
        estado = estado_trabajador(t, hoy)
        if estado != EstadoDiario.Estado.TRABAJANDO:
            return error(f'{t.nombre} hoy figura como {EstadoDiario.Estado(estado).label}. '
                         'Actualice el pase de lista si es un error.')
        ParticipanteOrden.objects.create(
            orden=orden, trabajador=t, desde=hoy,
            motivo=str(request.data.get('motivo', ''))[:200], agregado_por=request.user,
        )
        self._nota(orden, f'Se agregó al participante {t.nombre}')

        # Aviso (no bloquea): ya participa en otra orden abierta
        avisos = []
        otras = (ParticipanteOrden.objects
                 .filter(trabajador=t, hasta__isnull=True, orden__estado__in=[E.REGISTRADA, E.EN_EJECUCION])
                 .exclude(orden=orden).select_related('orden'))
        for p in otras:
            avisos.append(f'{t.nombre} también participa en la orden abierta {p.orden.codigo}.')
        return self.salida(orden, avisos)

    @action(detail=True, methods=['post'])
    def retirar_participante(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'editar')):
            return e
        n = orden.participantes.filter(
            trabajador_id=request.data.get('trabajador'), hasta__isnull=True
        ).update(hasta=timezone.localdate())
        if not n:
            return error('Ese trabajador no es participante vigente.')
        self._nota(orden, 'Un participante dejó la orden (queda registrado con su fecha de fin)')
        return self.salida(orden)

    @action(detail=True, methods=['post'])
    def agregar_brigada(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'editar')):
            return e
        brigada = Brigada.objects.filter(pk=request.data.get('brigada'), uo=orden.uo, activa=True).first()
        if brigada is None:
            return error('Brigada no válida.')
        if orden.brigadas.filter(brigada=brigada, hasta__isnull=True).exists():
            return error('Esa brigada ya está asignada a la orden.')
        reemplazar = request.data.get('reemplazar') in (True, 'true', 1, '1')
        with transaction.atomic():
            if reemplazar:
                for b in orden.brigadas.filter(hasta__isnull=True).select_related('brigada'):
                    cerrar_brigada(orden, b.brigada)
            avisos = agregar_brigada_a_orden(orden, brigada, request.user)
            self._nota(orden, f'Brigada asignada: {brigada.nombre}' + (' (reemplaza a la anterior)' if reemplazar else ''))
        return self.salida(orden, avisos)

    @action(detail=True, methods=['post'])
    def retirar_brigada(self, request, pk=None):
        orden = self.get_object()
        if (e := self._permitido(orden, 'editar')):
            return e
        brigada = Brigada.objects.filter(pk=request.data.get('brigada'), uo=orden.uo).first()
        if brigada is None or not orden.brigadas.filter(brigada=brigada, hasta__isnull=True).exists():
            return error('Esa brigada no está vigente en la orden.')
        with transaction.atomic():
            cerrar_brigada(orden, brigada)
            self._nota(orden, f'Brigada retirada: {brigada.nombre}')
        return self.salida(orden)


class GenerarOrdenView(APIView):
    """POST /api/solicitudes/<id>/generar-orden/  (solo el Especialista)."""
    permission_classes = [TienePerfil]

    def post(self, request, pk):
        perfil = request.user.perfil
        if perfil.rol != Perfil.Rol.ESPECIALISTA:
            return error('Solo el Especialista genera las órdenes de trabajo.', status.HTTP_403_FORBIDDEN)
        solicitud = get_object_or_404(Solicitud, pk=pk, uo=perfil.uo)
        if solicitud.estado != Solicitud.Estado.EN_PROGRAMACION:
            return error('La solicitud debe estar En programación (con la inspección registrada).')
        if hasattr(solicitud, 'orden'):
            return error('Esta solicitud ya tiene una orden de trabajo.')

        hoy = timezone.localdate()
        brigada = vehiculo = None
        if request.data.get('brigada'):
            brigada = Brigada.objects.filter(pk=request.data['brigada'], uo=perfil.uo, activa=True).first()
            if brigada is None:
                return error('Brigada no válida.')
        if request.data.get('vehiculo'):
            vehiculo = Vehiculo.objects.filter(pk=request.data['vehiculo'], uo=perfil.uo, activo=True).first()
            if vehiculo is None:
                return error('Vehículo no válido.')
            if estado_vehiculo(vehiculo, hoy) != EstadoVehiculo.Estado.DISPONIBLE:
                return error(f'El vehículo {vehiculo.chapa} no está disponible hoy.')

        # Quién hizo la inspección: el usuario que pasó la solicitud a "En programación"
        h = (solicitud.historial.filter(estado_nuevo=Solicitud.Estado.EN_PROGRAMACION)
             .select_related('usuario').order_by('-fecha').first())
        inspeccion = (h.usuario.get_full_name() or h.usuario.username) if h else ''

        with transaction.atomic():
            orden = Orden.objects.create(
                uo=perfil.uo, anio=hoy.year, numero=Orden.siguiente_numero(perfil.uo, hoy.year),
                tipo=Orden.Tipo.CORRECTIVO, solicitud=solicitud,
                inmueble=solicitud.inmueble, centro_costo=solicitud.centro_costo,
                area_solicitante=solicitud.area_solicitante, local=solicitud.local,
                cliente=solicitud.solicitante,
                afectacion=solicitud.afectacion.nombre if solicitud.afectacion_id else solicitud.otra_afectacion,
                descripcion_solicitud=solicitud.descripcion, inspeccion_por=inspeccion,
                vehiculo=vehiculo, fecha_solicitud=solicitud.creada.date(),
            )
            HistorialOrden.objects.create(
                orden=orden, estado_nuevo=orden.estado, usuario=request.user, comentario='Orden registrada',
            )
            avisos = agregar_brigada_a_orden(orden, brigada, request.user) if brigada else []

            anterior = solicitud.estado
            solicitud.estado = Solicitud.Estado.ORDEN_GENERADA
            solicitud.save()
            HistorialEstado.objects.create(
                solicitud=solicitud, estado_anterior=anterior, estado_nuevo=solicitud.estado,
                usuario=request.user, comentario=f'Se generó la orden de trabajo {orden.codigo}',
            )
        return Response({'id': orden.id, 'codigo': orden.codigo, 'avisos': avisos}, status=status.HTTP_201_CREATED)
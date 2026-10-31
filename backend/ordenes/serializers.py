from django.utils import timezone
from rest_framework import serializers

from accounts.models import Perfil
from personal.models import EstadoDiario
from personal.utils import estado_trabajador
from transporte.models import EstadoVehiculo
from transporte.utils import estado_vehiculo
from .models import Orden
from .reglas import acciones_permitidas, proxima_firma
from recursos.models import LineaRecurso, SolicitudRecurso

ROLES = dict(Perfil.Rol.choices)


class OrdenSerializer(serializers.ModelSerializer):
    """Salida completa de una orden (solo lectura)."""
    codigo = serializers.CharField(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)
    inmueble_nombre = serializers.CharField(source='inmueble.denominacion', read_only=True)
    area_nombre = serializers.CharField(source='area_solicitante.nombre', read_only=True)
    local_nombre = serializers.CharField(source='local.nombre', read_only=True, default=None)
    centro_costo_nombre = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    vehiculo_texto = serializers.SerializerMethodField()
    brigadas = serializers.SerializerMethodField()
    participantes = serializers.SerializerMethodField()
    firmas = serializers.SerializerMethodField()
    proxima_firma = serializers.SerializerMethodField()
    historial = serializers.SerializerMethodField()
    acciones = serializers.SerializerMethodField()
    materiales = serializers.SerializerMethodField()
    valor_total = serializers.SerializerMethodField()
    recursos = serializers.SerializerMethodField()

    def _despachados(self, obj):
        return (LineaRecurso.objects
                .filter(solicitud__orden=obj, solicitud__estado=SolicitudRecurso.Estado.DESPACHADA,
                        cantidad_despachada__gt=0)
                .select_related('material', 'solicitud'))

    def get_materiales(self, obj):
        return [
            {'vale': l.solicitud.vale_numero, 'codigo': l.material.codigo_sap,
             'descripcion': l.material.descripcion, 'um': l.material.unidad_medida,
             'cantidad': l.cantidad_despachada, 'precio': l.precio_unitario,
             'importe': round(l.cantidad_despachada * l.precio_unitario, 2)}
            for l in self._despachados(obj)
        ]

    def get_valor_total(self, obj):
        return round(sum((l.cantidad_despachada * l.precio_unitario for l in self._despachados(obj)), 0), 2)

    def get_recursos(self, obj):
        return [{'id': s.id, 'codigo': s.codigo, 'estado': s.get_estado_display()}
                for s in obj.solicitudes_recursos.all()]

    class Meta:
        model = Orden
        fields = [
            'id', 'codigo', 'uo_acronimo', 'tipo', 'tipo_display', 'estado', 'estado_display',
            'solicitud', 'inmueble_nombre', 'area_nombre', 'local_nombre', 'centro_costo_nombre',
            'cliente_nombre', 'afectacion', 'descripcion_solicitud', 'inspeccion_por',
            'vehiculo', 'vehiculo_texto', 'descripcion_trabajos', 'incidencias',
            'fecha_solicitud', 'fecha_cierre', 'creada',
            'brigadas', 'participantes', 'firmas', 'proxima_firma', 'historial', 'acciones',
            'materiales', 'valor_total', 'recursos'
        ]
        read_only_fields = fields

    def get_centro_costo_nombre(self, obj):
        return str(obj.centro_costo)

    def get_cliente_nombre(self, obj):
        return (obj.cliente.get_full_name() or obj.cliente.username) if obj.cliente else ''

    def get_vehiculo_texto(self, obj):
        return str(obj.vehiculo) if obj.vehiculo else ''

    def get_brigadas(self, obj):
        return [
            {'brigada': b.brigada_id, 'nombre': b.brigada.nombre, 'desde': b.desde,
             'hasta': b.hasta, 'vigente': b.hasta is None}
            for b in obj.brigadas.all()
        ]

    def get_participantes(self, obj):
        hoy = timezone.localdate()
        filas = []
        for p in obj.participantes.all():
            vigente = p.hasta is None
            estado = estado_trabajador(p.trabajador, hoy) if vigente else None
            filas.append({
                'trabajador': p.trabajador_id, 'nombre': p.trabajador.nombre,
                'desde': p.desde, 'hasta': p.hasta, 'vigente': vigente, 'motivo': p.motivo,
                'estado_hoy': estado,
                # Alerta: participa pero hoy no figura como Trabajando
                'alerta': vigente and estado != EstadoDiario.Estado.TRABAJANDO,
            })
        return filas

    def get_firmas(self, obj):
        return [
            {'rol': f.rol, 'rol_display': ROLES.get(f.rol, f.rol),
             'usuario': f.usuario.get_full_name() or f.usuario.username, 'fecha': f.fecha}
            for f in obj.firmas.all()
        ]

    def get_proxima_firma(self, obj):
        return proxima_firma(obj) if obj.estado == Orden.Estado.CONFORME else None

    def get_historial(self, obj):
        return [
            {'estado_anterior': h.estado_anterior, 'estado_nuevo': h.estado_nuevo,
             'usuario': h.usuario.get_full_name() or h.usuario.username,
             'comentario': h.comentario, 'fecha': h.fecha}
            for h in obj.historial.all()
        ]

    def get_acciones(self, obj):
        return acciones_permitidas(obj, self.context['request'].user)


class OrdenEdicionSerializer(serializers.ModelSerializer):
    """Los únicos datos que se editan directamente en una orden."""

    class Meta:
        model = Orden
        fields = ['descripcion_trabajos', 'incidencias', 'vehiculo']

    def validate_vehiculo(self, vehiculo):
        if vehiculo is None or vehiculo == self.instance.vehiculo:
            return vehiculo
        if vehiculo.uo_id != self.instance.uo_id or not vehiculo.activo:
            raise serializers.ValidationError('Vehículo no válido para su UO.')
        if estado_vehiculo(vehiculo, timezone.localdate()) != EstadoVehiculo.Estado.DISPONIBLE:
            raise serializers.ValidationError(f'El vehículo {vehiculo.chapa} no está disponible hoy.')
        return vehiculo
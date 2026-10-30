from rest_framework import serializers
from .models import Solicitud, HistorialEstado
from .transiciones import puede_transicionar


class HistorialSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = HistorialEstado
        fields = ['estado_anterior', 'estado_nuevo', 'usuario', 'comentario', 'fecha']


class SolicitudSerializer(serializers.ModelSerializer):
    inmueble_nombre = serializers.CharField(source='inmueble.denominacion', read_only=True)
    area_nombre = serializers.CharField(source='area_solicitante.nombre', read_only=True)
    local_nombre = serializers.CharField(source='local.nombre', read_only=True)
    afectacion_nombre = serializers.CharField(source='afectacion.nombre', read_only=True, default=None)
    solicitante_nombre = serializers.CharField(source='solicitante.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    historial = HistorialSerializer(many=True, read_only=True)
    acciones_permitidas = serializers.SerializerMethodField()

    class Meta:
        model = Solicitud
        fields = [
            'id', 'uo', 'inmueble', 'inmueble_nombre', 'centro_costo',
            'area_solicitante', 'area_nombre', 'local', 'local_nombre',
            'afectacion', 'afectacion_nombre', 'otra_afectacion',
            'descripcion', 'foto',
            'solicitante', 'solicitante_nombre', 'estado', 'estado_display',
            'es_urgente', 'motivo_devolucion', 'creada', 'actualizada',
            'historial', 'acciones_permitidas',
        ]
        # El cliente NO puede fijar estos campos: los pone el servidor
        read_only_fields = ['uo', 'solicitante', 'estado', 'es_urgente', 'motivo_devolucion']

    def get_acciones_permitidas(self, obj):
        perfil = self.context['request'].user.perfil
        return [e for e in Solicitud.Estado.values if puede_transicionar(obj, e, perfil)]

    def validate(self, datos):
        uo = self.context['request'].user.perfil.uo

        def valor(campo, defecto=None):
            return datos.get(campo, getattr(self.instance, campo, defecto))

        # Inmueble, centro de costo y área deben ser de la UO del usuario
        for campo, texto in (('inmueble', 'El inmueble'), ('centro_costo', 'El centro de costo'),
                             ('area_solicitante', 'El área')):
            obj = datos.get(campo)
            if obj is not None and obj.uo_id != uo.id:
                raise serializers.ValidationError({campo: f'{texto} no pertenece a su UO.'})

        # El local debe ser del inmueble elegido
        inmueble, local = valor('inmueble'), valor('local')
        if inmueble is not None and local is not None and local.inmueble_id != inmueble.id:
            raise serializers.ValidationError({'local': 'El local no pertenece al inmueble seleccionado.'})

        # Afectación: de la lista, o escrita a mano
        afectacion = valor('afectacion')
        otra = (valor('otra_afectacion', '') or '').strip()
        if afectacion is None and not otra:
            raise serializers.ValidationError({'afectacion': 'Seleccione la afectación o indique cuál es.'})
        datos['otra_afectacion'] = '' if afectacion is not None else otra
        return datos



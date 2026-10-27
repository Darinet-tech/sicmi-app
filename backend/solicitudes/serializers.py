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
    solicitante_nombre = serializers.CharField(source='solicitante.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    historial = HistorialSerializer(many=True, read_only=True)

    acciones_permitidas = serializers.SerializerMethodField()

    def get_acciones_permitidas(self, obj):
        perfil = self.context['request'].user.perfil
        return [e for e in Solicitud.Estado.values if puede_transicionar(obj, e, perfil)]

    class Meta:
        model = Solicitud
        fields = [
            'id', 'uo', 'inmueble', 'inmueble_nombre', 'centro_costo',
            'area_solicitante', 'local', 'descripcion', 'foto',
            'solicitante', 'solicitante_nombre', 'estado', 'estado_display',
            'es_urgente', 'motivo_devolucion', 'creada', 'actualizada', 'historial','acciones_permitidas',
        ]
        # El cliente NO puede fijar estos campos: los pone el servidor
        read_only_fields = ['uo', 'solicitante', 'estado', 'es_urgente', 'motivo_devolucion']

    def validate(self, datos):
        """El inmueble y el centro de costo deben ser de la UO del usuario."""
        uo = self.context['request'].user.perfil.uo
        if 'inmueble' in datos and datos['inmueble'].uo_id != uo.id:
            raise serializers.ValidationError('El inmueble no pertenece a su UO.')
        if 'centro_costo' in datos and datos['centro_costo'].uo_id != uo.id:
            raise serializers.ValidationError('El centro de costo no pertenece a su UO.')
        return datos



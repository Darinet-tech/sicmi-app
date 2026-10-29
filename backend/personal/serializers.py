from rest_framework import serializers
from .models import Trabajador, Brigada


class TrabajadorSerializer(serializers.ModelSerializer):
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)

    class Meta:
        model = Trabajador
        fields = ['id', 'nombre', 'cargo', 'activo', 'uo_acronimo']


class BrigadaSerializer(serializers.ModelSerializer):
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)
    jefe_nombre = serializers.CharField(source='jefe.nombre', read_only=True, default=None)
    miembros = serializers.SerializerMethodField()

    class Meta:
        model = Brigada
        fields = ['id', 'nombre', 'jefe', 'jefe_nombre', 'activa', 'miembros', 'uo_acronimo']

    def get_miembros(self, obj):
        return [
            {'id': m.trabajador_id, 'nombre': m.trabajador.nombre, 'cargo': m.trabajador.cargo}
            for m in obj.miembros.all() if m.hasta is None
        ]

    def validate_jefe(self, jefe):
        uo = self.context['request'].user.perfil.uo
        if jefe and jefe.uo_id != uo.id:
            raise serializers.ValidationError('El jefe debe ser un trabajador de su UO.')
        return jefe

    def validate_nombre(self, nombre):
        uo = self.context['request'].user.perfil.uo
        qs = Brigada.objects.filter(uo=uo, nombre__iexact=nombre)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe una brigada con ese nombre.')
        return nombre
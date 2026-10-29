from rest_framework import serializers
from .models import Vehiculo


class VehiculoSerializer(serializers.ModelSerializer):
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)

    class Meta:
        model = Vehiculo
        fields = ['id', 'chapa', 'tipo', 'descripcion', 'activo', 'uo_acronimo']

    def validate_chapa(self, chapa):
        chapa = chapa.strip().upper()
        uo = self.context['request'].user.perfil.uo
        qs = Vehiculo.objects.filter(uo=uo, chapa=chapa)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un vehículo con esa chapa en su UO.')
        return chapa
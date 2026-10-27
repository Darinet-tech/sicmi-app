from rest_framework import serializers
from .models import Inmueble, CentroCosto


class InmuebleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inmueble
        fields = ['id', 'denominacion', 'direccion']


class CentroCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroCosto
        fields = ['id', 'codigo', 'nombre']
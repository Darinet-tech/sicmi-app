from rest_framework import serializers
from .models import (
    GrupoGenerico, Inmueble, CentroCosto, Departamento,
    CentroTelefonico, AreaSolicitante, Local,
)


class InmuebleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inmueble
        fields = ['id', 'denominacion', 'direccion']


class CentroCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroCosto
        fields = ['id', 'codigo', 'nombre']


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['id', 'acronimo', 'nombre']


class CentroTelefonicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroTelefonico
        fields = ['id', 'codigo', 'nombre', 'tipo']


class AreaSolicitanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaSolicitante
        fields = ['id', 'nombre']


class LocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Local
        fields = ['id', 'nombre', 'inmueble']


class GrupoGenericoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoGenerico
        fields = ['id', 'numero', 'nombre']
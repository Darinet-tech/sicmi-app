from rest_framework import serializers
from .models import Trabajador, Brigada


class TrabajadorBasicoSerializer(serializers.ModelSerializer):
    """Datos no sensibles: para los roles que no deben ver salario, carnet, etc."""
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)

    class Meta:
        model = Trabajador
        fields = ['id', 'codigo', 'nombre', 'cargo', 'cargo_display', 'categoria',
                  'departamento', 'activo', 'uo_acronimo']


class TrabajadorSerializer(serializers.ModelSerializer):
    """Ficha completa."""
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)

    class Meta:
        model = Trabajador
        exclude = ['uo', 'usuario']

    def validate_codigo(self, codigo):
        codigo = codigo.strip().upper()
        uo = self.context['request'].user.perfil.uo
        qs = Trabajador.objects.filter(uo=uo, codigo=codigo)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un trabajador con ese código en su UO.')
        return codigo

    def validate(self, datos):
        def valor(campo):
            return datos.get(campo, getattr(self.instance, campo, None))

        # Licencia: si tiene, el número y la categoría son obligatorios; si no, se vacían
        if valor('licencia_conduccion'):
            if not valor('numero_licencia'):
                raise serializers.ValidationError({'numero_licencia': 'Indique el número de licencia.'})
            if not valor('categoria_licencia'):
                raise serializers.ValidationError({'categoria_licencia': 'Indique la categoría de la licencia.'})
        else:
            datos['numero_licencia'] = ''
            datos['categoria_licencia'] = ''

        # Un Jefe de Departamento solo puede ser categoría A, B o C
        if valor('cargo') == Trabajador.Cargo.JEFE_DEPARTAMENTO and valor('categoria') not in ('A', 'B', 'C'):
            raise serializers.ValidationError(
                {'categoria': 'Un Jefe de Departamento solo puede ser categoría A, B o C.'})
        return datos


class BrigadaSerializer(serializers.ModelSerializer):
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)
    jefe_nombre = serializers.CharField(source='jefe.nombre', read_only=True, default=None)
    miembros = serializers.SerializerMethodField()

    class Meta:
        model = Brigada
        fields = ['id', 'nombre', 'jefe', 'jefe_nombre', 'activa', 'miembros', 'uo_acronimo']

    def get_miembros(self, obj):
        return [
            {'id': m.trabajador_id, 'nombre': m.trabajador.nombre,
             'cargo': m.trabajador.get_cargo_display()}
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
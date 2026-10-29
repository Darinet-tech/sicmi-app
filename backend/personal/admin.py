from django.contrib import admin
from .models import Trabajador, EstadoDiario, Brigada, MiembroBrigada


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'cargo', 'categoria', 'uo', 'activo')
    list_filter = ('uo', 'cargo', 'activo')
    search_fields = ('codigo', 'nombre', 'carnet_identidad')
    fieldsets = (
        ('Datos personales', {'fields': (
            'uo', 'codigo', 'nombre', 'carnet_identidad', 'nivel_escolar', 'direccion', 'activo')}),
        ('Puesto', {'fields': (
            'cargo', 'categoria', 'departamento', 'centro_principal',
            'centro_asociado', 'numero_plaza', 'salario')}),
        ('Licencia de conducción', {'fields': (
            'licencia_conduccion', 'numero_licencia', 'categoria_licencia')}),
        ('Contacto', {'fields': ('movil', 'telefono_particular', 'telefono_oficina')}),
        ('Opcional: usuario del sistema', {'fields': ('usuario',), 'classes': ('collapse',)}),
    )


admin.site.register(EstadoDiario)
admin.site.register(Brigada)
admin.site.register(MiembroBrigada)
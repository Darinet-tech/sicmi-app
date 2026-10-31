from django.contrib import admin
from .models import (Almacen, Material, Existencia, PresupuestoAnual,
                     Sobregiro, SolicitudRecurso, LineaRecurso)


@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'uo')
    list_filter = ('uo',)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('codigo_sap', 'descripcion', 'unidad_medida')
    search_fields = ('codigo_sap', 'descripcion')


@admin.register(Existencia)
class ExistenciaAdmin(admin.ModelAdmin):
    list_display = ('material', 'almacen', 'cantidad_libre', 'valor_unitario', 'actualizada')
    list_filter = ('almacen',)
    search_fields = ('material__codigo_sap', 'material__descripcion')


@admin.register(PresupuestoAnual)
class PresupuestoAnualAdmin(admin.ModelAdmin):
    list_display = ('uo', 'anio', 'monto')
    list_filter = ('anio', 'uo')


class LineaInline(admin.TabularInline):
    model = LineaRecurso
    extra = 0


@admin.register(SolicitudRecurso)
class SolicitudRecursoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'uo', 'orden', 'estado', 'creada')
    list_filter = ('uo', 'estado')
    inlines = [LineaInline]


admin.site.register(Sobregiro)
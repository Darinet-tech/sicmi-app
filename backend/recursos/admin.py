from django.contrib import admin
from .models import Almacen, Material, Existencia


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
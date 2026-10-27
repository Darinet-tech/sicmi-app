from django.contrib import admin
from .models import GrupoGenerico, Inmueble, CentroCosto


@admin.register(GrupoGenerico)
class GrupoGenericoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre')


@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ('denominacion', 'uo', 'activo')
    list_filter = ('uo', 'activo')
    search_fields = ('denominacion', 'direccion')


@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'uo')
    list_filter = ('uo',)
    search_fields = ('codigo', 'nombre')
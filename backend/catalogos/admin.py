from django.contrib import admin
from .models import (
    GrupoGenerico, Inmueble, CentroCosto, Departamento,
    CentroTelefonico, AreaSolicitante, Local,
)


@admin.register(GrupoGenerico)
class GrupoGenericoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre')


class LocalInline(admin.TabularInline):
    model = Local
    extra = 2


@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ('denominacion', 'uo', 'activo')
    list_filter = ('uo', 'activo')
    search_fields = ('denominacion', 'direccion')
    inlines = [LocalInline]


@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'uo')
    list_filter = ('uo',)
    search_fields = ('codigo', 'nombre')


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('acronimo', 'nombre', 'uo')
    list_filter = ('uo',)
    search_fields = ('acronimo', 'nombre')

@admin.register(CentroTelefonico)
class CentroTelefonicoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo', 'uo')
    list_filter = ('uo', 'tipo')


@admin.register(AreaSolicitante)
class AreaSolicitanteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'uo')
    list_filter = ('uo',)


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'inmueble', 'activo')
    list_filter = ('inmueble__uo', 'inmueble')
    search_fields = ('nombre',)
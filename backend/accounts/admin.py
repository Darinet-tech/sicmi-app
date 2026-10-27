from django.contrib import admin
from .models import UnidadOrganizativa, Perfil


@admin.register(UnidadOrganizativa)
class UnidadOrganizativaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'activa')
    search_fields = ('codigo', 'nombre')


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'uo', 'cargo')
    list_filter = ('rol', 'uo')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
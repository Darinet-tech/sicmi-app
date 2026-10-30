from rest_framework import viewsets

from solicitudes.permissions import TienePerfil
from .models import (
    GrupoGenerico, Inmueble, CentroCosto, Departamento,
    CentroTelefonico, AreaSolicitante, Local,
)
from .serializers import (
    GrupoGenericoSerializer, InmuebleSerializer, CentroCostoSerializer,
    DepartamentoSerializer, CentroTelefonicoSerializer,
    AreaSolicitanteSerializer, LocalSerializer,
)


class FiltroPorUOMixin:
    """Cada usuario ve solo los datos de su UO (el nivel central ve todos)."""
    permission_classes = [TienePerfil]

    def filtrar(self, qs):
        perfil = self.request.user.perfil
        return qs if perfil.es_central else qs.filter(uo=perfil.uo)


class InmuebleViewSet(FiltroPorUOMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = InmuebleSerializer

    def get_queryset(self):
        return self.filtrar(Inmueble.objects.filter(activo=True))


class CentroCostoViewSet(FiltroPorUOMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CentroCostoSerializer

    def get_queryset(self):
        return self.filtrar(CentroCosto.objects.all())


class DepartamentoViewSet(FiltroPorUOMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DepartamentoSerializer

    def get_queryset(self):
        return self.filtrar(Departamento.objects.all())


class CentroTelefonicoViewSet(FiltroPorUOMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CentroTelefonicoSerializer

    def get_queryset(self):
        qs = self.filtrar(CentroTelefonico.objects.all())
        tipo = self.request.query_params.get('tipo')
        return qs.filter(tipo=tipo) if tipo else qs


class AreaSolicitanteViewSet(FiltroPorUOMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AreaSolicitanteSerializer

    def get_queryset(self):
        return self.filtrar(AreaSolicitante.objects.all())


class LocalViewSet(viewsets.ReadOnlyModelViewSet):
    """Locales de los inmuebles de la UO. Filtro opcional: ?inmueble=ID"""
    permission_classes = [TienePerfil]
    serializer_class = LocalSerializer

    def get_queryset(self):
        perfil = self.request.user.perfil
        qs = Local.objects.filter(activo=True).select_related('inmueble')
        if not perfil.es_central:
            qs = qs.filter(inmueble__uo=perfil.uo)
        inmueble = self.request.query_params.get('inmueble')
        if inmueble and inmueble.isdigit():
            qs = qs.filter(inmueble_id=inmueble)
        return qs


class GrupoGenericoViewSet(viewsets.ReadOnlyModelViewSet):
    """Afectaciones (grupos genéricos): iguales para toda la empresa."""
    permission_classes = [TienePerfil]
    serializer_class = GrupoGenericoSerializer
    queryset = GrupoGenerico.objects.all()
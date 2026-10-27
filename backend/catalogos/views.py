from rest_framework import viewsets

from solicitudes.permissions import TienePerfil
from .models import Inmueble, CentroCosto
from .serializers import InmuebleSerializer, CentroCostoSerializer


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
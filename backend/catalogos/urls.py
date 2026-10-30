from rest_framework.routers import DefaultRouter
from .views import (
    InmuebleViewSet, CentroCostoViewSet, DepartamentoViewSet,
    CentroTelefonicoViewSet, AreaSolicitanteViewSet, LocalViewSet, GrupoGenericoViewSet,
)

router = DefaultRouter()
router.register('inmuebles', InmuebleViewSet, basename='inmueble')
router.register('centros-costo', CentroCostoViewSet, basename='centro-costo')
router.register('departamentos', DepartamentoViewSet, basename='departamento')
router.register('centros-telefonicos', CentroTelefonicoViewSet, basename='centro-telefonico')
router.register('areas', AreaSolicitanteViewSet, basename='area')
router.register('locales', LocalViewSet, basename='local')
router.register('grupos-genericos', GrupoGenericoViewSet, basename='grupo-generico')
urlpatterns = router.urls
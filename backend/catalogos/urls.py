from rest_framework.routers import DefaultRouter
from .views import InmuebleViewSet, CentroCostoViewSet

router = DefaultRouter()
router.register('inmuebles', InmuebleViewSet, basename='inmueble')
router.register('centros-costo', CentroCostoViewSet, basename='centro-costo')
urlpatterns = router.urls
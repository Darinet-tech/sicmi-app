from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TrabajadorViewSet, BrigadaViewSet, PaseListaView

router = DefaultRouter()
router.register('trabajadores', TrabajadorViewSet, basename='trabajador')
router.register('brigadas', BrigadaViewSet, basename='brigada')

urlpatterns = router.urls + [
    path('pase-lista/', PaseListaView.as_view(), name='pase-lista'),
]
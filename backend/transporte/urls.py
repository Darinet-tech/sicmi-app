from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import VehiculoViewSet, ParteTransporteView

router = DefaultRouter()
router.register('vehiculos', VehiculoViewSet, basename='vehiculo')

urlpatterns = router.urls + [
    path('parte-transporte/', ParteTransporteView.as_view(), name='parte-transporte'),
]
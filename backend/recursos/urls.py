from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (SolicitudRecursoViewSet, SobregiroViewSet, AlmacenViewSet,
                    PresupuestoView, ExistenciasView)

router = DefaultRouter()
router.register('solicitudes-recursos', SolicitudRecursoViewSet, basename='solicitud-recurso')
router.register('sobregiros', SobregiroViewSet, basename='sobregiro')
router.register('almacenes', AlmacenViewSet, basename='almacen')

urlpatterns = router.urls + [
    path('presupuesto/', PresupuestoView.as_view(), name='presupuesto'),
    path('existencias/', ExistenciasView.as_view(), name='existencias'),
]
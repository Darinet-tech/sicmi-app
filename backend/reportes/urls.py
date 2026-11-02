from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CertificacionViewSet, SeriesView, IndicadoresView, UnidadesView

router = DefaultRouter()
router.register('certificaciones', CertificacionViewSet, basename='certificacion')

urlpatterns = router.urls + [
    path('reportes/series/', SeriesView.as_view(), name='reportes-series'),
    path('reportes/indicadores/', IndicadoresView.as_view(), name='reportes-indicadores'),
    path('reportes/unidades/', UnidadesView.as_view(), name='reportes-unidades'),
]
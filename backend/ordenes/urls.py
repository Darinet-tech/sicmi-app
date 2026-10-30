from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import OrdenViewSet, GenerarOrdenView

router = DefaultRouter()
router.register('ordenes', OrdenViewSet, basename='orden')

urlpatterns = router.urls + [
    path('solicitudes/<int:pk>/generar-orden/', GenerarOrdenView.as_view(), name='generar-orden'),
]
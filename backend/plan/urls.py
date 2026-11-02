from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, AccionViewSet, ClientesView

router = DefaultRouter()
router.register('planes', PlanViewSet, basename='plan')
router.register('acciones-plan', AccionViewSet, basename='accion-plan')

urlpatterns = router.urls + [
    path('plan-clientes/', ClientesView.as_view(), name='plan-clientes'),
]
from django.urls import path
from .views import (
    AnexoSolicitud, AnexoRegistroOrdenes, AnexoRecursos,
    AnexoSobregiro, AnexoAprobacion, AnexoOrden,
    AnexoPlan, AnexoTareaTecnica, AnexoCroquis,
)

urlpatterns = [
    path('solicitud/<int:pk>/', AnexoSolicitud.as_view()),
    path('registro-ordenes/', AnexoRegistroOrdenes.as_view()),
    path('recursos/<int:pk>/', AnexoRecursos.as_view()),
    path('sobregiro/<int:pk>/', AnexoSobregiro.as_view()),
    path('aprobacion-sobregiro/<int:pk>/', AnexoAprobacion.as_view()),
    path('orden/<int:pk>/', AnexoOrden.as_view()),
    path('plan/<int:pk>/', AnexoPlan.as_view()),
    path('tarea-tecnica/<int:pk>/', AnexoTareaTecnica.as_view()),
    path('croquis/<int:pk>/', AnexoCroquis.as_view()),
]
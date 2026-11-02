from django.urls import path
from . import views

urlpatterns = [
    path('salud/', views.salud, name='salud'),
    path('yo/', views.yo, name='yo'),
    path('bienvenida/vista/', views.bienvenida_vista, name='bienvenida-vista'),
]
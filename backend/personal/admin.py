from django.contrib import admin
from .models import Trabajador, EstadoDiario, Brigada, MiembroBrigada

admin.site.register(Trabajador)
admin.site.register(EstadoDiario)
admin.site.register(Brigada)
admin.site.register(MiembroBrigada)
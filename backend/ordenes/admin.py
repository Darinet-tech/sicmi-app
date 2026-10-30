from django.contrib import admin
from .models import Orden, BrigadaOrden, ParticipanteOrden, Firma, HistorialOrden

admin.site.register(Orden)
admin.site.register(BrigadaOrden)
admin.site.register(ParticipanteOrden)
admin.site.register(Firma)
admin.site.register(HistorialOrden)

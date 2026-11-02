from django.contrib import admin
from .models import Certificacion, CertificacionFirma, HistorialCertificacion

admin.site.register(Certificacion)
admin.site.register(CertificacionFirma)
admin.site.register(HistorialCertificacion)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import LoginView

admin.site.site_header = 'SiCMI - Administración'
admin.site.site_title = 'SiCMI'
admin.site.index_title = 'Sistema de Control del Mantenimiento a Inmuebles'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('catalogos.urls')),
    path('api/', include('solicitudes.urls')),
    path('api/', include('personal.urls')),
    path('api/', include('transporte.urls')),
    path('api/', include('ordenes.urls')),
    path('api/', include('recursos.urls')),
    path('api/', include('plan.urls')),
    path('api/', include('reportes.urls')),
    path('api/anexos/', include('anexos.urls')),
    path('api/token/', LoginView.as_view(), name='token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Solo en desarrollo: en producción las fotos y croquis los sirve el servidor web
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
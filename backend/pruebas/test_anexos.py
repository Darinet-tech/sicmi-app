import shutil
import tempfile
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from plan.models import PlanAnual, TareaTecnica
from recursos.models import Sobregiro, SolicitudRecurso
from .base import Entorno, orden_en_proceso, recurso_despachado
from .test_plan import crear_plan


class AnexosTest(APITestCase):
    """Cada anexo se genera en PDF y Excel sin errores (los errores de reportlab/openpyxl aparecen aquí)."""

    def setUp(self):
        # Los croquis subidos en la prueba van a una carpeta temporal, no a su carpeta de datos
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, True)
        ajuste = override_settings(MEDIA_ROOT=media)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

        self.e = e = Entorno('AAA')
        hoy = timezone.localdate()
        esp = e.api('ESPECIALISTA')

        # Orden generada, con materiales despachados y una devolución (Anexos 1, 2, 3 y 6)
        self.solicitud, oid = orden_en_proceso(e)
        rid = recurso_despachado(e, oid)
        linea = SolicitudRecurso.objects.get(pk=rid).lineas.get()
        r = e.api('BALANCISTA').post(f'/api/solicitudes-recursos/{rid}/registrar_sobrante/', {
            'linea': linea.id, 'cantidad': '1', 'destino': 'DEVOLUCION', 'vale_devolucion': 'D-1'}, format='json')
        assert r.status_code == 200, r.data
        assert esp.post(f'/api/ordenes/{oid}/generar/').status_code == 200

        # Plan aprobado con tarea técnica y croquis (Anexos 7, 8 y 9)
        plan, accion = crear_plan(e, PlanAnual.Estado.APROBADO, es_compleja=True)
        TareaTecnica.objects.create(
            accion=accion, descripcion_general='Cubierta de fibrocemento',
            trabajos=[{'desperfecto': 'Gotera', 'trabajo': 'Sustituir tejas', 'um': 'm2', 'cantidad': '12'}],
            elaborado_nombre='Elena Especialista', elaborado_cargo='Especialista')
        buf = BytesIO()
        Image.new('RGB', (300, 200), 'white').save(buf, 'PNG')
        r = esp.post(f'/api/acciones-plan/{accion.id}/croquis/', {
            'imagen': SimpleUploadedFile('croquis.png', buf.getvalue(), content_type='image/png'),
            'plano_no': '1', 'escala': '1:50'}, format='multipart')
        assert r.status_code == 200, r.data

        # Sobregiro aprobado (Anexos 4 y 5)
        director = e.usuarios['DIRECTOR_UO']
        sob = Sobregiro.objects.create(
            uo=e.uo, anio=hoy.year, financiamiento_asignado=Decimal('1000'), real_gastado=Decimal('900'),
            monto_solicitado=Decimal('200'), fundamentacion='Más averías', estado='APROBADO',
            monto_aprobado=Decimal('200'), respuesta='Aprobado', solicitado_por=director,
            resuelto_por=director, resuelto=timezone.now())

        # Certificación mensual (Anexo 10)
        r = esp.post('/api/certificaciones/', {'anio': hoy.year, 'mes': hoy.month}, format='json')
        assert r.status_code == 201, r.data

        self.anexos = {
            'Anexo 1': (f'/api/anexos/solicitud/{self.solicitud.id}/', {}),
            'Anexo 2': ('/api/anexos/registro-ordenes/', {'anio': hoy.year}),
            'Anexo 3 salida': (f'/api/anexos/recursos/{rid}/', {'tipo': 'salida'}),
            'Anexo 3 devolución': (f'/api/anexos/recursos/{rid}/', {'tipo': 'devolucion'}),
            'Anexo 4': (f'/api/anexos/sobregiro/{sob.id}/', {}),
            'Anexo 5': (f'/api/anexos/aprobacion-sobregiro/{sob.id}/', {}),
            'Anexo 6': (f'/api/anexos/orden/{oid}/', {}),
            'Anexo 7': (f'/api/anexos/tarea-tecnica/{accion.id}/', {}),
            'Anexo 8': (f'/api/anexos/croquis/{accion.id}/', {}),
            'Anexo 9': (f'/api/anexos/plan/{plan.id}/', {}),
            'Anexo 10': (f'/api/anexos/certificacion/{r.data["id"]}/', {}),
        }

    def test_todos_los_anexos_se_generan_en_pdf_y_excel(self):
        esp = self.e.api('ESPECIALISTA')
        for nombre, (ruta, params) in self.anexos.items():
            for formato, firma in (('pdf', b'%PDF'), ('xlsx', b'PK')):
                with self.subTest(anexo=nombre, formato=formato):
                    r = esp.get(ruta, {**params, 'formato': formato})
                    self.assertEqual(r.status_code, 200, getattr(r, 'data', r.content[:200]))
                    self.assertTrue(r.content.startswith(firma))
                    self.assertGreater(len(r.content), 1000)

    def test_el_cliente_no_obtiene_anexos_ajenos(self):
        otra = Entorno('BBB')
        r = otra.api('CLIENTE').get(f'/api/anexos/solicitud/{self.solicitud.id}/')
        self.assertEqual(r.status_code, 404)
        r = self.e.api('CLIENTE').get('/api/anexos/registro-ordenes/')
        self.assertEqual(r.status_code, 403)
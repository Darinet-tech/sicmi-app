from django.utils import timezone
from rest_framework.test import APITestCase

from ordenes.models import Orden
from .base import Entorno, crear_solicitud


class ReportesTest(APITestCase):
    def setUp(self):
        self.e = Entorno('AAA')
        self.hoy = timezone.localdate()

    def test_no_se_certifica_un_mes_futuro(self):
        anio = self.hoy.year + (self.hoy.month == 12)
        mes = 1 if self.hoy.month == 12 else self.hoy.month + 1
        r = self.e.api('ESPECIALISTA').post('/api/certificaciones/', {'anio': anio, 'mes': mes}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_certificacion_con_cadena_de_firmas(self):
        esp = self.e.api('ESPECIALISTA')
        r = esp.post('/api/certificaciones/', {'anio': self.hoy.year, 'mes': self.hoy.month}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        cid = r.data['id']
        self.assertEqual(r.data['estado'], 'BORRADOR')
        # No se repite el mismo mes
        r = esp.post('/api/certificaciones/', {'anio': self.hoy.year, 'mes': self.hoy.month}, format='json')
        self.assertEqual(r.status_code, 400)

        base = f'/api/certificaciones/{cid}'
        self.assertEqual(esp.post(f'{base}/enviar/').data['estado'], 'EN_FIRMAS')
        # El Jefe de Logística firma al final, no antes que el Jefe de Grupo
        self.assertEqual(self.e.api('JEFE_LOGISTICA').post(f'{base}/firmar/').status_code, 403)
        self.assertEqual(self.e.api('JEFE_GRUPO').post(f'{base}/firmar/').status_code, 200)
        r = self.e.api('JEFE_LOGISTICA').post(f'{base}/firmar/')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['estado'], 'APROBADA')

    def test_indicador_de_satisfaccion(self):
        e, hoy = self.e, self.hoy
        resuelta = crear_solicitud(e)
        crear_solicitud(e)  # recibida y todavía sin resolver
        Orden.objects.create(
            uo=e.uo, anio=hoy.year, numero=1, tipo='MC', solicitud=resuelta, inmueble=e.inmueble,
            centro_costo=e.centro, area_solicitante=e.area, cliente=e.usuarios['CLIENTE'],
            estado=Orden.Estado.CERRADA, fecha_solicitud=hoy, fecha_cierre=hoy)
        r = e.api('ESPECIALISTA').get('/api/reportes/indicadores/', {'anio': hoy.year, 'mes': hoy.month})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['satisfaccion']['mes'], {'a': 1, 'b': 2, 'pct': 50})

    def test_series_de_los_graficos(self):
        api = self.e.api('ESPECIALISTA')
        for periodo, cantidad in (('semana', 8), ('mes', 12), ('anio', 5)):
            r = api.get('/api/reportes/series/', {'periodo': periodo, 'anio': self.hoy.year})
            self.assertEqual(r.status_code, 200, (periodo, r.data))
            self.assertEqual(len(r.data['etiquetas']), cantidad)
        self.assertEqual(api.get('/api/reportes/series/', {'periodo': 'dia'}).status_code, 400)
        self.assertEqual(self.e.api('CLIENTE').get('/api/reportes/series/').status_code, 403)
from rest_framework.test import APITestCase

from catalogos.models import Inmueble, Local
from solicitudes.models import Solicitud
from .base import Entorno, crear_solicitud


class SolicitudesTest(APITestCase):
    def setUp(self):
        self.e = Entorno('AAA')

    def datos(self, **extra):
        d = {'inmueble': self.e.inmueble.id, 'centro_costo': self.e.centro.id,
             'area_solicitante': self.e.area.id, 'local': self.e.local.id,
             'afectacion': self.e.grupo.id, 'descripcion': 'Salidero en el baño'}
        d.update(extra)
        return d

    def test_el_cliente_no_puede_fijar_estado_ni_urgencia(self):
        r = self.e.api('CLIENTE').post('/api/solicitudes/', self.datos(estado='CERRADA', es_urgente=True), format='json')
        self.assertEqual(r.status_code, 201, r.data)
        s = Solicitud.objects.get(pk=r.data['id'])
        self.assertEqual(s.estado, 'ENVIADA')
        self.assertFalse(s.es_urgente)
        self.assertEqual(s.uo, self.e.uo)
        self.assertEqual(s.solicitante, self.e.usuarios['CLIENTE'])

    def test_la_afectacion_es_obligatoria_o_se_escribe(self):
        sin = self.datos()
        del sin['afectacion']
        self.assertEqual(self.e.api('CLIENTE').post('/api/solicitudes/', sin, format='json').status_code, 400)
        otra = dict(sin, otra_afectacion='Pared agrietada')
        self.assertEqual(self.e.api('CLIENTE').post('/api/solicitudes/', otra, format='json').status_code, 201)

    def test_solo_el_cliente_crea_solicitudes(self):
        r = self.e.api('ESPECIALISTA').post('/api/solicitudes/', self.datos(), format='json')
        self.assertEqual(r.status_code, 403)

    def test_rechaza_un_inmueble_de_otra_uo(self):
        otra = Entorno('BBB')
        r = self.e.api('CLIENTE').post('/api/solicitudes/', self.datos(inmueble=otra.inmueble.id), format='json')
        self.assertEqual(r.status_code, 400)

    def test_el_local_debe_ser_del_inmueble(self):
        inm2 = Inmueble.objects.create(uo=self.e.uo, denominacion='Otro inmueble')
        loc2 = Local.objects.create(inmueble=inm2, nombre='Sala')
        r = self.e.api('CLIENTE').post('/api/solicitudes/', self.datos(local=loc2.id), format='json')
        self.assertEqual(r.status_code, 400)

    def test_flujo_de_revision_a_programacion(self):
        s = crear_solicitud(self.e)
        url = f'/api/solicitudes/{s.id}/cambiar_estado/'
        # El cliente no puede mover su propia solicitud por el flujo
        r = self.e.api('CLIENTE').post(url, {'estado': 'EN_INSPECCION'}, format='json')
        self.assertEqual(r.status_code, 403)
        # Logística revisa y aprueba para inspección
        lg = self.e.api('JEFE_LOGISTICA')
        self.assertEqual(lg.post(url, {'estado': 'EN_REVISION'}, format='json').status_code, 200)
        self.assertEqual(lg.post(url, {'estado': 'EN_INSPECCION'}, format='json').status_code, 200)
        # Al registrar la inspección es obligatorio decidir si es urgente
        jb = self.e.api('JEFE_BRIGADA')
        self.assertEqual(jb.post(url, {'estado': 'EN_PROGRAMACION'}, format='json').status_code, 400)
        r = jb.post(url, {'estado': 'EN_PROGRAMACION', 'es_urgente': True}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        s.refresh_from_db()
        self.assertEqual(s.estado, 'EN_PROGRAMACION')
        self.assertTrue(s.es_urgente)

    def test_devolver_exige_motivo_y_el_cliente_corrige(self):
        s = crear_solicitud(self.e, Solicitud.Estado.EN_REVISION)
        url = f'/api/solicitudes/{s.id}/cambiar_estado/'
        jg = self.e.api('JEFE_GRUPO')
        self.assertEqual(jg.post(url, {'estado': 'DEVUELTA'}, format='json').status_code, 400)
        r = jg.post(url, {'estado': 'DEVUELTA', 'comentario': 'Falta el local exacto'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        s.refresh_from_db()
        self.assertEqual(s.motivo_devolucion, 'Falta el local exacto')
        cli = self.e.api('CLIENTE')
        r = cli.patch(f'/api/solicitudes/{s.id}/', {'descripcion': 'Corregida'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(cli.post(url, {'estado': 'ENVIADA'}, format='json').status_code, 200)

    def test_el_cliente_no_edita_fuera_de_devuelta(self):
        s = crear_solicitud(self.e)
        r = self.e.api('CLIENTE').patch(f'/api/solicitudes/{s.id}/', {'descripcion': 'Cambio'}, format='json')
        self.assertEqual(r.status_code, 403)
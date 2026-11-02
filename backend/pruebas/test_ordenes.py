from django.utils import timezone
from rest_framework.test import APITestCase

from ordenes.models import Orden
from .base import (Entorno, orden_en_proceso, orden_generada, pedir_recursos,
                   recurso_despachado, solicitud_programada)


class OrdenesTest(APITestCase):
    def setUp(self):
        self.e = Entorno('AAA')

    def llevar_a_entregada(self, oid):
        jb = self.e.api('JEFE_BRIGADA')
        r = jb.post(f'/api/ordenes/{oid}/iniciar/')
        self.assertEqual(r.status_code, 200, r.data)
        r = jb.patch(f'/api/ordenes/{oid}/editar/', {'descripcion_trabajos': 'Se reparó el salidero'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        r = jb.post(f'/api/ordenes/{oid}/entregar/')
        self.assertEqual(r.status_code, 200, r.data)

    def test_la_orden_nace_en_proceso_sin_numero(self):
        s, oid = orden_en_proceso(self.e)
        o = Orden.objects.get(pk=oid)
        self.assertEqual(o.estado, 'EN_PROCESO')
        self.assertIsNone(o.numero)
        self.assertTrue(o.codigo.startswith('BORR-'))
        self.assertEqual(o.participantes.filter(hasta__isnull=True).count(), 3)
        self.assertEqual(o.inspeccion_por, self.e.usuarios['JEFE_BRIGADA'].get_full_name())
        s.refresh_from_db()
        self.assertEqual(s.estado, 'EN_PROGRAMACION')

    def test_solo_el_especialista_prepara_y_una_sola_vez(self):
        s = solicitud_programada(self.e)
        url = f'/api/solicitudes/{s.id}/generar-orden/'
        self.assertEqual(self.e.api('JEFE_BRIGADA').post(url, {}, format='json').status_code, 403)
        self.assertEqual(self.e.api('ESPECIALISTA').post(url, {}, format='json').status_code, 201)
        self.assertEqual(self.e.api('ESPECIALISTA').post(url, {}, format='json').status_code, 400)

    def test_no_se_genera_sin_el_vale_de_salida(self):
        _, oid = orden_en_proceso(self.e)
        r = self.e.api('ESPECIALISTA').post(f'/api/ordenes/{oid}/generar/')
        self.assertEqual(r.status_code, 400)
        self.assertIn('vale', r.data['detalle'])
        self.assertIsNone(Orden.objects.get(pk=oid).numero)

    def test_sin_materiales_se_genera_con_su_numero(self):
        s, oid = orden_generada(self.e)
        o = Orden.objects.get(pk=oid)
        self.assertEqual(o.estado, 'REGISTRADA')
        self.assertEqual(o.codigo, f'{timezone.localdate().year % 100:02d}-001')
        s.refresh_from_db()
        self.assertEqual(s.estado, 'ORDEN_GENERADA')

    def test_el_consecutivo_es_por_uo(self):
        otra = Entorno('BBB')
        orden_generada(self.e)
        orden_generada(self.e)
        orden_generada(otra)
        self.assertEqual(sorted(Orden.objects.filter(uo=self.e.uo).values_list('numero', flat=True)), [1, 2])
        self.assertEqual(list(Orden.objects.filter(uo=otra.uo).values_list('numero', flat=True)), [1])

    def test_vale_de_salida_y_confirmacion_de_sobrantes(self):
        _, oid = orden_en_proceso(self.e)
        esp = self.e.api('ESPECIALISTA')
        rid = recurso_despachado(self.e, oid)
        self.assertEqual(esp.post(f'/api/ordenes/{oid}/generar/').status_code, 200)

        jb = self.e.api('JEFE_BRIGADA')
        self.assertEqual(jb.post(f'/api/ordenes/{oid}/iniciar/').status_code, 200)
        jb.patch(f'/api/ordenes/{oid}/editar/', {'descripcion_trabajos': 'Listo'}, format='json')
        r = jb.post(f'/api/ordenes/{oid}/entregar/')
        self.assertEqual(r.status_code, 400)
        self.assertIn('sobrantes', r.data['detalle'])
        r = self.e.api('BALANCISTA').post(f'/api/solicitudes-recursos/{rid}/revisar_sobrantes/')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(jb.post(f'/api/ordenes/{oid}/entregar/').status_code, 200)

    def test_una_orden_con_recursos_pendientes_no_se_genera(self):
        _, oid = orden_en_proceso(self.e)
        pedir_recursos(self.e, oid)  # solicitada, sin despachar
        r = self.e.api('ESPECIALISTA').post(f'/api/ordenes/{oid}/generar/')
        self.assertEqual(r.status_code, 400)

    def test_cadena_de_firmas_y_cierre(self):
        s, oid = orden_generada(self.e)
        self.llevar_a_entregada(oid)
        # Sin la conformidad del cliente nadie puede firmar
        r = self.e.api('JEFE_BRIGADA').post(f'/api/ordenes/{oid}/firmar/')
        self.assertEqual(r.status_code, 403)
        r = self.e.api('CLIENTE').post(f'/api/ordenes/{oid}/conformidad/', {'conforme': True}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        # El Especialista firma al final, no primero
        self.assertEqual(self.e.api('ESPECIALISTA').post(f'/api/ordenes/{oid}/firmar/').status_code, 403)
        for rol in ('JEFE_BRIGADA', 'JEFE_GRUPO', 'ESPECIALISTA'):
            r = self.e.api(rol).post(f'/api/ordenes/{oid}/firmar/')
            self.assertEqual(r.status_code, 200, (rol, r.data))
        o = Orden.objects.get(pk=oid)
        self.assertEqual(o.estado, 'CERRADA')
        self.assertIsNotNone(o.fecha_cierre)
        s.refresh_from_db()
        self.assertEqual(s.estado, 'CERRADA')

    def test_no_conformidad_devuelve_la_orden_a_ejecucion(self):
        _, oid = orden_generada(self.e)
        self.llevar_a_entregada(oid)
        cli = self.e.api('CLIENTE')
        url = f'/api/ordenes/{oid}/conformidad/'
        self.assertEqual(cli.post(url, {'conforme': False}, format='json').status_code, 400)
        r = cli.post(url, {'conforme': False, 'comentario': 'Quedó una gotera'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(Orden.objects.get(pk=oid).estado, 'EN_EJECUCION')

    def test_el_cliente_no_ve_las_ordenes_en_proceso(self):
        _, oid = orden_en_proceso(self.e)
        cli = self.e.api('CLIENTE')
        self.assertEqual(cli.get('/api/ordenes/').data, [])
        self.assertEqual(cli.get(f'/api/ordenes/{oid}/').status_code, 404)
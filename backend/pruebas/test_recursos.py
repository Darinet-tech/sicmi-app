from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from recursos.models import Existencia, PresupuestoAnual, SolicitudRecurso
from .base import Entorno, api_de, crear_central, orden_en_proceso, pedir_recursos, recurso_despachado, recurso_hasta


class RecursosTest(APITestCase):
    def setUp(self):
        self.e = Entorno('AAA')
        _, self.oid = orden_en_proceso(self.e)

    def presupuesto(self, clave):
        r = self.e.api('DIRECTOR_UO').get('/api/presupuesto/', {'anio': timezone.localdate().year})
        self.assertEqual(r.status_code, 200)
        return Decimal(str(r.data[0][clave]))

    def test_no_se_puede_pedir_mas_de_lo_que_hay(self):
        r = pedir_recursos(self.e, self.oid, '51')  # en el almacén hay 50
        self.assertEqual(r.status_code, 400)
        self.assertEqual(SolicitudRecurso.objects.count(), 0)

    def test_verificacion_dentro_del_presupuesto(self):
        rid = recurso_hasta(self.e, self.oid, 'verificar')
        self.assertEqual(SolicitudRecurso.objects.get(pk=rid).estado, 'VERIFICADA')

    def test_presupuesto_insuficiente_pide_sobregiro(self):
        PresupuestoAnual.objects.filter(uo=self.e.uo).update(monto=Decimal('20'))
        r = pedir_recursos(self.e, self.oid, '5')  # 5 x 10 = 50 CUP
        rid = r.data['id']
        esp = self.e.api('ESPECIALISTA')
        r = esp.post(f'/api/solicitudes-recursos/{rid}/verificar/')
        self.assertEqual(r.data['estado'], 'PENDIENTE_SOBREGIRO')

        r = self.e.api('DIRECTOR_UO').post(
            '/api/sobregiros/', {'monto_solicitado': '100', 'fundamentacion': 'Más averías'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        r = api_de(crear_central()).post(
            f'/api/sobregiros/{r.data["id"]}/resolver/', {'aprobar': True, 'monto_aprobado': '100'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)

        r = esp.post(f'/api/solicitudes-recursos/{rid}/verificar/')
        self.assertEqual(r.data['estado'], 'VERIFICADA')

    def test_solo_el_director_solicita_sobregiros(self):
        r = self.e.api('ESPECIALISTA').post(
            '/api/sobregiros/', {'monto_solicitado': '100', 'fundamentacion': 'x'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_autorizar_compromete_y_despachar_gasta(self):
        recurso_hasta(self.e, self.oid, 'autorizar')
        self.assertEqual(self.presupuesto('comprometido'), Decimal('50'))
        self.assertEqual(self.presupuesto('disponible'), Decimal('950'))

        rid = SolicitudRecurso.objects.get().id
        r = self.e.api('BALANCISTA').post(
            f'/api/solicitudes-recursos/{rid}/despachar/', {'vale_numero': 'V-77'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(self.presupuesto('comprometido'), Decimal('0'))
        self.assertEqual(self.presupuesto('gastado'), Decimal('50'))
        self.assertEqual(self.presupuesto('disponible'), Decimal('950'))
        self.e.existencia.refresh_from_db()
        self.assertEqual(self.e.existencia.cantidad_libre, Decimal('45'))

    def test_la_devolucion_restaura_la_existencia_y_baja_el_gasto(self):
        rid = recurso_despachado(self.e, self.oid, '5')
        linea = SolicitudRecurso.objects.get(pk=rid).lineas.get()
        url = f'/api/solicitudes-recursos/{rid}/registrar_sobrante/'
        bal = self.e.api('BALANCISTA')
        cuerpo = {'linea': linea.id, 'cantidad': '2', 'destino': 'DEVOLUCION'}
        self.assertEqual(bal.post(url, cuerpo, format='json').status_code, 400)  # falta el vale
        r = bal.post(url, dict(cuerpo, vale_devolucion='D-1'), format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.e.existencia.refresh_from_db()
        self.assertEqual(self.e.existencia.cantidad_libre, Decimal('47'))
        self.assertEqual(self.presupuesto('gastado'), Decimal('30'))
        # No se puede justificar más de lo despachado (quedan 3 por justificar)
        r = bal.post(url, dict(cuerpo, cantidad='4', vale_devolucion='D-2'), format='json')
        self.assertEqual(r.status_code, 400)

    def test_el_despacho_exige_el_numero_de_vale(self):
        rid = recurso_hasta(self.e, self.oid, 'autorizar')
        r = self.e.api('BALANCISTA').post(f'/api/solicitudes-recursos/{rid}/despachar/', {}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(SolicitudRecurso.objects.get(pk=rid).estado, 'AUTORIZADA')

    def test_la_existencia_nunca_queda_negativa(self):
        rid = recurso_hasta(self.e, self.oid, 'autorizar')
        Existencia.objects.filter(pk=self.e.existencia.pk).update(cantidad_libre=Decimal('1'))
        r = self.e.api('BALANCISTA').post(
            f'/api/solicitudes-recursos/{rid}/despachar/', {'vale_numero': 'V-9'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.e.existencia.refresh_from_db()
        self.assertEqual(self.e.existencia.cantidad_libre, Decimal('1'))
        self.assertEqual(SolicitudRecurso.objects.get(pk=rid).estado, 'AUTORIZADA')
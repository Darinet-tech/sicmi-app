from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from ordenes.models import Orden
from plan.models import AccionPlan, PlanAnual, TareaTecnica
from .base import Entorno


def crear_plan(e, estado=PlanAnual.Estado.BORRADOR, **accion):
    plan = PlanAnual.objects.create(
        uo=e.uo, anio=timezone.localdate().year + 1, estado=estado, elaborado_por=e.usuarios['ESPECIALISTA'])
    datos = dict(plan=plan, inmueble=e.inmueble, grupo=e.grupo, via=AccionPlan.Via.PROPIOS,
                 programacion={'3': 1}, valor_estimado=Decimal('1.5'))
    datos.update(accion)
    return plan, AccionPlan.objects.create(**datos)


class PlanTest(APITestCase):
    def setUp(self):
        self.e = Entorno('AAA')

    def cuerpo_orden(self, mes=3):
        return {'mes': mes, 'centro_costo': self.e.centro.id, 'area_solicitante': self.e.area.id,
                'cliente': self.e.usuarios['CLIENTE'].id}

    def test_cadena_de_firmas_hasta_aprobar(self):
        plan, _ = crear_plan(self.e)
        base = f'/api/planes/{plan.id}'
        r = self.e.api('ESPECIALISTA').post(f'{base}/enviar/')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['estado'], 'EN_FIRMAS')
        # El Director no puede saltarse a quienes firman antes
        self.assertEqual(self.e.api('DIRECTOR_UO').post(f'{base}/firmar/').status_code, 403)
        for rol in ('JEFE_GRUPO', 'JEFE_LOGISTICA', 'DIRECTOR_UO'):
            r = self.e.api(rol).post(f'{base}/firmar/')
            self.assertEqual(r.status_code, 200, (rol, r.data))
        plan.refresh_from_db()
        self.assertEqual(plan.estado, 'APROBADO')
        # Aprobado: ya no se pueden agregar obras
        r = self.e.api('ESPECIALISTA').post('/api/acciones-plan/', {
            'plan': plan.id, 'inmueble': self.e.inmueble.id, 'grupo': self.e.grupo.id,
            'programacion': {'4': 1}, 'valor_estimado': '1'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_devolver_borra_las_firmas_y_exige_motivo(self):
        plan, _ = crear_plan(self.e)
        base = f'/api/planes/{plan.id}'
        self.e.api('ESPECIALISTA').post(f'{base}/enviar/')
        jg = self.e.api('JEFE_GRUPO')
        self.assertEqual(jg.post(f'{base}/devolver/', {}, format='json').status_code, 400)
        r = jg.post(f'{base}/devolver/', {'motivo': 'Falta detalle'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        plan.refresh_from_db()
        self.assertEqual(plan.estado, 'BORRADOR')
        self.assertEqual(plan.firmas.count(), 0)

    def test_un_plan_no_aprobado_no_genera_ordenes(self):
        _, accion = crear_plan(self.e)
        r = self.e.api('ESPECIALISTA').post(
            f'/api/acciones-plan/{accion.id}/generar-orden/', self.cuerpo_orden(), format='json')
        self.assertEqual(r.status_code, 400)

    def test_cupo_mensual_de_ordenes(self):
        _, accion = crear_plan(self.e, PlanAnual.Estado.APROBADO)
        esp = self.e.api('ESPECIALISTA')
        url = f'/api/acciones-plan/{accion.id}/generar-orden/'
        r = esp.post(url, self.cuerpo_orden(), format='json')
        self.assertEqual(r.status_code, 201, r.data)
        oid = r.data['id']
        self.assertEqual(esp.post(url, self.cuerpo_orden(), format='json').status_code, 400)       # sin cupo
        self.assertEqual(esp.post(url, self.cuerpo_orden(mes=4), format='json').status_code, 400)  # no programado
        # Al cancelar la orden se libera el cupo
        r = esp.post(f'/api/ordenes/{oid}/cancelar/', {'comentario': 'Se pospone'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(esp.post(url, self.cuerpo_orden(), format='json').status_code, 201)

    def test_obra_compleja_exige_tarea_tecnica(self):
        _, accion = crear_plan(self.e, PlanAnual.Estado.APROBADO, es_compleja=True)
        esp = self.e.api('ESPECIALISTA')
        url = f'/api/acciones-plan/{accion.id}/generar-orden/'
        self.assertEqual(esp.post(url, self.cuerpo_orden(), format='json').status_code, 400)
        TareaTecnica.objects.create(
            accion=accion, descripcion_general='Cubierta de fibrocemento',
            trabajos=[{'desperfecto': 'Gotera', 'trabajo': 'Sustituir tejas', 'um': 'm2', 'cantidad': '12'}])
        self.assertEqual(esp.post(url, self.cuerpo_orden(), format='json').status_code, 201)

    def test_la_orden_preventiva_nace_en_proceso_y_enlazada_al_plan(self):
        _, accion = crear_plan(self.e, PlanAnual.Estado.APROBADO)
        esp = self.e.api('ESPECIALISTA')
        r = esp.post(f'/api/acciones-plan/{accion.id}/generar-orden/', self.cuerpo_orden(), format='json')
        self.assertEqual(r.status_code, 201, r.data)
        o = Orden.objects.get(pk=r.data['id'])
        self.assertEqual(o.tipo, 'MP')
        self.assertEqual(o.estado, 'EN_PROCESO')
        self.assertEqual(o.accion_plan, accion)
        self.assertEqual(o.mes_plan, 3)
        self.assertIsNone(o.solicitud)
        self.assertTrue(esp.get(f'/api/ordenes/{o.id}/').data['plan_texto'])
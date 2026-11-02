from rest_framework.test import APITestCase

from accounts.models import Perfil
from .base import Entorno, User, api_de, crear_central, crear_solicitud, orden_generada


class AislamientoPorUOTest(APITestCase):
    """Cada UO ve solo lo suyo; el cliente ve solo lo suyo; el nivel central ve todo."""

    def setUp(self):
        self.a = Entorno('AAA')
        self.b = Entorno('BBB')
        self.sol_a = crear_solicitud(self.a)
        self.sol_b = crear_solicitud(self.b)

    def test_listado_solo_de_su_uo(self):
        r = self.b.api('JEFE_LOGISTICA').get('/api/solicitudes/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([s['id'] for s in r.data], [self.sol_b.id])

    def test_detalle_de_otra_uo_no_existe(self):
        r = self.b.api('JEFE_LOGISTICA').get(f'/api/solicitudes/{self.sol_a.id}/')
        self.assertEqual(r.status_code, 404)

    def test_cliente_solo_ve_sus_solicitudes(self):
        otro = self.a.nuevo_usuario('cliente2_aaa', 'CLIENTE')
        crear_solicitud(self.a, solicitante=otro)
        r = self.a.api('CLIENTE').get('/api/solicitudes/')
        self.assertEqual([s['id'] for s in r.data], [self.sol_a.id])

    def test_nivel_central_ve_todas_las_uo(self):
        r = api_de(crear_central()).get('/api/solicitudes/')
        self.assertEqual({s['id'] for s in r.data}, {self.sol_a.id, self.sol_b.id})

    def test_ordenes_aisladas_por_uo(self):
        _, oid = orden_generada(self.a)
        self.assertEqual(self.b.api('ESPECIALISTA').get('/api/ordenes/').data, [])
        self.assertEqual(self.b.api('ESPECIALISTA').get(f'/api/ordenes/{oid}/').status_code, 404)

    def test_datos_sensibles_del_personal(self):
        r = self.a.api('JEFE_BRIGADA').get('/api/trabajadores/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.data) > 0)
        self.assertNotIn('salario', r.data[0])
        self.assertNotIn('carnet_identidad', r.data[0])
        r = self.a.api('ESPECIALISTA').get('/api/trabajadores/')
        self.assertIn('salario', r.data[0])

    def test_cliente_no_accede_al_personal(self):
        self.assertEqual(self.a.api('CLIENTE').get('/api/trabajadores/').status_code, 403)

    def test_usuario_sin_perfil_no_entra(self):
        u = User.objects.create(username='sinperfil')
        self.assertEqual(api_de(u).get('/api/solicitudes/').status_code, 403)
        self.assertEqual(api_de(u).get('/api/yo/').status_code, 403)


class AccesoTest(APITestCase):
    def test_login_correcto_e_incorrecto(self):
        u = User.objects.create_user('ana', password='Prueba2026*')
        Perfil.objects.create(usuario=u, uo=None, rol='CENTRAL')
        r = self.client.post('/api/token/', {'username': 'ana', 'password': 'Prueba2026*'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)
        r = self.client.post('/api/token/', {'username': 'ana', 'password': 'incorrecta'}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_yo_y_bienvenida(self):
        e = Entorno('AAA')
        api = e.api('CLIENTE')
        r = api.get('/api/yo/')
        self.assertEqual(r.data['rol'], 'CLIENTE')
        self.assertFalse(r.data['bienvenida_vista'])
        self.assertEqual(api.post('/api/bienvenida/vista/').status_code, 200)
        self.assertTrue(api.get('/api/yo/').data['bienvenida_vista'])
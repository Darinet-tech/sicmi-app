"""Datos y funciones de apoyo para las pruebas automáticas."""
import itertools
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Perfil, UnidadOrganizativa
from catalogos.models import (AreaSolicitante, CentroCosto, CentroTelefonico, Departamento,
                              GrupoGenerico, Inmueble, Local)
from personal.models import Brigada, MiembroBrigada, Trabajador
from recursos.models import Almacen, Existencia, Material, PresupuestoAnual
from solicitudes.models import HistorialEstado, Solicitud
from transporte.models import Vehiculo

User = get_user_model()

ROLES = ['CLIENTE', 'JEFE_LOGISTICA', 'JEFE_GRUPO', 'JEFE_BRIGADA', 'ESPECIALISTA', 'BALANCISTA', 'DIRECTOR_UO']
_carnets = itertools.count(1)


def api_de(usuario):
    """Cliente HTTP que actúa como ese usuario."""
    c = APIClient()
    c.force_authenticate(usuario)
    return c


def crear_central():
    u = User.objects.create(username='central_prueba', first_name='Central', last_name='Prueba')
    Perfil.objects.create(usuario=u, uo=None, rol='CENTRAL')
    return u


class Entorno:
    """Una UO completa: un usuario por rol, catálogos, personal, brigada, almacén y presupuesto."""

    def __init__(self, acronimo='AAA'):
        hoy = timezone.localdate()
        self.uo = UnidadOrganizativa.objects.create(acronimo=acronimo, nombre=f'Unidad {acronimo}')
        self.usuarios = {rol: self.nuevo_usuario(f'{rol.lower()}_{acronimo.lower()}', rol) for rol in ROLES}

        # Catálogos
        self.inmueble = Inmueble.objects.create(uo=self.uo, denominacion=f'Inmueble {acronimo}')
        self.local = Local.objects.create(inmueble=self.inmueble, nombre='Pantry')
        self.centro = CentroCosto.objects.create(uo=self.uo, codigo='CC-1', nombre='Centro de prueba')
        self.area = AreaSolicitante.objects.create(uo=self.uo, nombre='Área de prueba')
        self.grupo, _ = GrupoGenerico.objects.get_or_create(numero=1, defaults={'nombre': 'Cimentaciones'})

        # Personal y brigada
        depto = Departamento.objects.create(uo=self.uo, acronimo='OP', nombre='Operaciones')
        ct = CentroTelefonico.objects.create(uo=self.uo, codigo='CT', nombre='Centro', tipo='PRINCIPAL')
        self.brigada = Brigada.objects.create(uo=self.uo, nombre='Brigada 1')
        self.trabajadores = []
        for n in range(1, 4):
            t = Trabajador.objects.create(
                uo=self.uo, codigo=f'{acronimo}{n}', nombre=f'Operario {acronimo}{n}',
                carnet_identidad=f'{next(_carnets):011d}', nivel_escolar='DOCE', direccion='Calle 1',
                cargo='OPERARIO', categoria='A', departamento=depto, centro_principal=ct,
                numero_plaza=f'P{n}', salario=Decimal('5000'))
            MiembroBrigada.objects.create(brigada=self.brigada, trabajador=t, desde=hoy)
            self.trabajadores.append(t)

        # Transporte, almacén y presupuesto
        self.vehiculo = Vehiculo.objects.create(uo=self.uo, chapa=f'B{acronimo}', tipo='Camioneta')
        self.almacen = Almacen.objects.create(uo=self.uo, codigo='0001', nombre='Principal')
        self.material = Material.objects.create(codigo_sap=f'MAT-{acronimo}', descripcion='Pintura', unidad_medida='U')
        self.existencia = Existencia.objects.create(
            almacen=self.almacen, material=self.material,
            cantidad_libre=Decimal('50'), valor_unitario=Decimal('10'))
        PresupuestoAnual.objects.create(uo=self.uo, anio=hoy.year, monto=Decimal('1000'))

    def nuevo_usuario(self, username, rol):
        u = User.objects.create(username=username, first_name=username.title(), last_name='Prueba')
        Perfil.objects.create(usuario=u, uo=self.uo, rol=rol, cargo=f'Cargo {rol}')
        return u

    def api(self, rol):
        return api_de(self.usuarios[rol])


# ------------------------------------------------------------------ flujos reutilizables
def crear_solicitud(e, estado=Solicitud.Estado.ENVIADA, solicitante=None):
    return Solicitud.objects.create(
        uo=e.uo, inmueble=e.inmueble, centro_costo=e.centro, area_solicitante=e.area, local=e.local,
        afectacion=e.grupo, descripcion='Fuga en el pantry',
        solicitante=solicitante or e.usuarios['CLIENTE'], estado=estado)


def solicitud_programada(e):
    """Solicitud ya inspeccionada (En programación), con su registro de quién inspeccionó."""
    s = crear_solicitud(e, Solicitud.Estado.EN_PROGRAMACION)
    HistorialEstado.objects.create(
        solicitud=s, estado_anterior='EN_INSPECCION', estado_nuevo='EN_PROGRAMACION',
        usuario=e.usuarios['JEFE_BRIGADA'])
    return s


def orden_en_proceso(e):
    """Devuelve (solicitud, id de la orden) con la orden creada En proceso y la brigada asignada."""
    s = solicitud_programada(e)
    r = e.api('ESPECIALISTA').post(
        f'/api/solicitudes/{s.id}/generar-orden/', {'brigada': e.brigada.id}, format='json')
    assert r.status_code == 201, r.data
    return s, r.data['id']


def orden_generada(e):
    """Orden con su número oficial (se marca «no requiere materiales» para poder generarla)."""
    s, oid = orden_en_proceso(e)
    esp = e.api('ESPECIALISTA')
    r = esp.patch(f'/api/ordenes/{oid}/editar/', {'sin_materiales': True}, format='json')
    assert r.status_code == 200, r.data
    r = esp.post(f'/api/ordenes/{oid}/generar/')
    assert r.status_code == 200, r.data
    return s, oid


def pedir_recursos(e, orden_id, cantidad='5'):
    return e.api('ESPECIALISTA').post('/api/solicitudes-recursos/', {
        'orden': orden_id, 'almacen': e.almacen.id,
        'lineas': [{'material': e.material.id, 'cantidad': cantidad}],
    }, format='json')


def recurso_hasta(e, orden_id, ultimo, cantidad='5'):
    """Lleva una solicitud de recursos por su ciclo hasta 'verificar', 'autorizar' o 'despachar'."""
    r = pedir_recursos(e, orden_id, cantidad)
    assert r.status_code == 201, r.data
    rid = r.data['id']
    pasos = [('ESPECIALISTA', 'verificar', {}), ('JEFE_LOGISTICA', 'autorizar', {}),
             ('BALANCISTA', 'despachar', {'vale_numero': 'V-001'})]
    for rol, accion, cuerpo in pasos:
        r = e.api(rol).post(f'/api/solicitudes-recursos/{rid}/{accion}/', cuerpo, format='json')
        assert r.status_code == 200, r.data
        if accion == ultimo:
            break
    return rid


def recurso_despachado(e, orden_id, cantidad='5'):
    return recurso_hasta(e, orden_id, 'despachar', cantidad)
from decimal import Decimal

from rest_framework import serializers

from .models import Almacen, Existencia, SolicitudRecurso
from .reglas import ABIERTAS, acciones_recurso
from .servicios import q2, resumen_presupuesto

S = SolicitudRecurso.Estado


def nombre(u):
    return (u.get_full_name() or u.username) if u else ''


class AlmacenSerializer(serializers.ModelSerializer):
    uo_acronimo = serializers.CharField(source='uo.acronimo', read_only=True)

    class Meta:
        model = Almacen
        fields = ['id', 'codigo', 'nombre', 'uo_acronimo']


def salida(sol, user, detalle=True):
    """Convierte una solicitud de recursos en un diccionario listo para enviar al frontend."""
    despachada = sol.estado == S.DESPACHADA
    filas, total = [], Decimal('0')
    for l in sol.lineas.all():
        base = l.cantidad_despachada if despachada else l.cantidad
        importe = base * l.precio_unitario
        total += importe
        fila = {
            'id': l.id, 'material': l.material_id, 'codigo_sap': l.material.codigo_sap,
            'descripcion': l.material.descripcion, 'um': l.material.unidad_medida,
            'cantidad': l.cantidad, 'cantidad_despachada': l.cantidad_despachada,
            'precio_unitario': l.precio_unitario, 'importe': q2(importe),
        }
        if detalle and sol.estado in ABIERTAS:
            fila['stock'] = (Existencia.objects.filter(almacen_id=sol.almacen_id, material_id=l.material_id)
                             .values_list('cantidad_libre', flat=True).first() or Decimal('0'))
        filas.append(fila)

    datos = {
        'id': sol.id, 'codigo': sol.codigo, 'estado': sol.estado,
        'estado_display': sol.get_estado_display(), 'uo_acronimo': sol.uo.acronimo,
        'orden': sol.orden_id, 'orden_codigo': sol.orden.codigo,
        'inmueble': sol.orden.inmueble.denominacion, 'centro_costo': str(sol.orden.centro_costo),
        'almacen': sol.almacen_id, 'almacen_nombre': str(sol.almacen),
        'solicitada_por': nombre(sol.solicitada_por), 'creada': sol.creada,
        'verificada_por': nombre(sol.verificada_por), 'fecha_verificacion': sol.fecha_verificacion,
        'autorizada_por': nombre(sol.autorizada_por), 'fecha_autorizacion': sol.fecha_autorizacion,
        'despachada_por': nombre(sol.despachada_por), 'fecha_despacho': sol.fecha_despacho,
        'vale_numero': sol.vale_numero, 'motivo': sol.motivo,
        'total': q2(total), 'lineas': filas,
    }
    if detalle:
        datos['presupuesto'] = resumen_presupuesto(sol.uo, sol.anio)
        datos['acciones'] = acciones_recurso(sol, user)
    return datos


def salida_sobregiro(s):
    return {
        'id': s.id, 'uo_acronimo': s.uo.acronimo, 'anio': s.anio,
        'financiamiento_asignado': s.financiamiento_asignado, 'real_gastado': s.real_gastado,
        'monto_solicitado': s.monto_solicitado, 'fundamentacion': s.fundamentacion,
        'estado': s.estado, 'estado_display': s.get_estado_display(),
        'monto_aprobado': s.monto_aprobado, 'respuesta': s.respuesta,
        'solicitado_por': nombre(s.solicitado_por), 'resuelto_por': nombre(s.resuelto_por),
        'creado': s.creado, 'resuelto': s.resuelto,
    }
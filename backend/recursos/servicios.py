from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from .models import Existencia, LineaRecurso, PresupuestoAnual, Sobrante, Sobregiro, SolicitudRecurso


CERO = Decimal('0')
D2 = Decimal('0.01')
DINERO = DecimalField(max_digits=22, decimal_places=4)
IMPORTE_SOLICITADO = ExpressionWrapper(F('cantidad') * F('precio_unitario'), output_field=DINERO)
IMPORTE_DESPACHADO = ExpressionWrapper(F('cantidad_despachada') * F('precio_unitario'), output_field=DINERO)
IMPORTE_SOBRANTE = ExpressionWrapper(F('cantidad') * F('linea__precio_unitario'), output_field=DINERO)


def q2(valor):
    return Decimal(valor).quantize(D2)


def resumen_presupuesto(uo, anio):
    """Asignado + sobregiros aprobados - gastado - comprometido = disponible.
    Gastado = despachado - devuelto al almacén (lo que queda en custodia sigue siendo gasto)."""
    p = PresupuestoAnual.objects.filter(uo=uo, anio=anio).first()
    asignado = p.monto if p else CERO
    sobregiros = (Sobregiro.objects.filter(uo=uo, anio=anio, estado=Sobregiro.Estado.APROBADO)
                  .aggregate(t=Sum('monto_aprobado'))['t'] or CERO)
    lineas = LineaRecurso.objects.filter(solicitud__uo=uo, solicitud__anio=anio)
    despachado = (lineas.filter(solicitud__estado=SolicitudRecurso.Estado.DESPACHADA)
                  .aggregate(t=Sum(IMPORTE_DESPACHADO))['t'] or CERO)
    devuelto = (Sobrante.objects
                .filter(destino=Sobrante.Destino.DEVOLUCION,
                        linea__solicitud__uo=uo, linea__solicitud__anio=anio)
                .aggregate(t=Sum(IMPORTE_SOBRANTE))['t'] or CERO)
    gastado = despachado - devuelto
    comprometido = (lineas.filter(solicitud__estado=SolicitudRecurso.Estado.AUTORIZADA)
                    .aggregate(t=Sum(IMPORTE_SOLICITADO))['t'] or CERO)
    return {
        'uo': uo.acronimo, 'anio': anio, 'configurado': p is not None,
        'asignado': q2(asignado), 'sobregiros_aprobados': q2(sobregiros),
        'gastado': q2(gastado), 'comprometido': q2(comprometido),
        'disponible': q2(asignado + sobregiros - gastado - comprometido),
    }


def total_estimado(solicitud):
    return sum((l.cantidad * l.precio_unitario for l in solicitud.lineas.all()), CERO)


def stock(almacen, material):
    e = Existencia.objects.filter(almacen=almacen, material=material).first()
    return e.cantidad_libre if e else CERO


def faltante(solicitud):
    """Devuelve un texto si alguna línea ya no tiene existencia suficiente; si todo bien, None."""
    for l in solicitud.lineas.select_related('material'):
        disponible = stock(solicitud.almacen, l.material)
        if l.cantidad > disponible:
            return (f'{l.material.codigo_sap}: se piden {l.cantidad} y en el almacén '
                    f'solo hay {disponible}.')
    return None


def _fila(vale, material, cantidad, precio, origen):
    return {
        'vale': vale, 'codigo': material.codigo_sap, 'descripcion': material.descripcion,
        'um': material.unidad_medida, 'cantidad': cantidad, 'precio': precio,
        'importe': q2(cantidad * precio), 'origen': origen,
    }


def materiales_de_orden(orden):
    """Materiales realmente utilizados en la orden:
    lo despachado menos lo devuelto o dejado en custodia, más los sobrantes de otras órdenes
    que se asignaron a esta."""
    filas = []
    lineas = (LineaRecurso.objects
              .filter(solicitud__orden=orden, solicitud__estado=SolicitudRecurso.Estado.DESPACHADA)
              .select_related('material', 'solicitud').prefetch_related('sobrantes'))
    for l in lineas:
        utilizada = l.cantidad_despachada - sum((s.cantidad for s in l.sobrantes.all()), CERO)
        if utilizada > 0:
            filas.append(_fila(l.solicitud.vale_numero, l.material, utilizada, l.precio_unitario, ''))

    recibidos = (Sobrante.objects.filter(orden_destino=orden)
                 .select_related('linea__material', 'linea__solicitud__orden'))
    for s in recibidos:
        l = s.linea
        filas.append(_fila(l.solicitud.vale_numero, l.material, s.cantidad, l.precio_unitario,
                           f'Sobrante de la orden {l.solicitud.orden.codigo}'))
    return filas
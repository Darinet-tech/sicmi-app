from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from .models import Existencia, LineaRecurso, PresupuestoAnual, Sobregiro, SolicitudRecurso

CERO = Decimal('0')
D2 = Decimal('0.01')
DINERO = DecimalField(max_digits=22, decimal_places=4)
IMPORTE_SOLICITADO = ExpressionWrapper(F('cantidad') * F('precio_unitario'), output_field=DINERO)
IMPORTE_DESPACHADO = ExpressionWrapper(F('cantidad_despachada') * F('precio_unitario'), output_field=DINERO)


def q2(valor):
    return Decimal(valor).quantize(D2)


def resumen_presupuesto(uo, anio):
    """Asignado + sobregiros aprobados - gastado - comprometido = disponible."""
    p = PresupuestoAnual.objects.filter(uo=uo, anio=anio).first()
    asignado = p.monto if p else CERO
    sobregiros = (Sobregiro.objects.filter(uo=uo, anio=anio, estado=Sobregiro.Estado.APROBADO)
                  .aggregate(t=Sum('monto_aprobado'))['t'] or CERO)
    lineas = LineaRecurso.objects.filter(solicitud__uo=uo, solicitud__anio=anio)
    gastado = (lineas.filter(solicitud__estado=SolicitudRecurso.Estado.DESPACHADA)
               .aggregate(t=Sum(IMPORTE_DESPACHADO))['t'] or CERO)
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
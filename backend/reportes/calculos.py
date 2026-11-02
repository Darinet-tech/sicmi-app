from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from ordenes.models import Orden
from personal.models import EstadoDiario
from plan.models import AccionPlan, PlanAnual
from recursos.models import (LineaRecurso, PresupuestoAnual, Sobrante, Sobregiro, SolicitudRecurso)
from recursos.servicios import IMPORTE_DESPACHADO, IMPORTE_SOBRANTE
from solicitudes.models import Solicitud
from transporte.models import EstadoVehiculo

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
MESES_ABR = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
GRUPO_OTRAS = 'Otras afectaciones (fuera de los grupos genéricos)'
CERO = Decimal('0')


def rango_mes(anio, mes):
    ini = date(anio, mes, 1)
    sig = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    return ini, sig - timedelta(days=1)


def pct(a, b):
    """Porcentaje en número entero (como indica el Anexo 10). None si no hay base."""
    return round(float(a) * 100 / float(b)) if b else None


# ---------------- piezas de cálculo ----------------
def acciones_plan(uos, anio):
    """Obras por medios propios de los planes APROBADOS de esas UO en ese año."""
    return list(AccionPlan.objects.filter(
        plan__uo__in=uos, plan__anio=anio, plan__estado=PlanAnual.Estado.APROBADO,
        via=AccionPlan.Via.PROPIOS).select_related('inmueble', 'grupo'))


def plan_en(acciones, meses):
    return sum(int(a.programacion.get(str(m), 0)) for a in acciones for m in meses)


def cerradas(uos, tipo, ini, fin):
    return Orden.objects.filter(uo__in=uos, tipo=tipo, estado=Orden.Estado.CERRADA,
                                fecha_cierre__range=(ini, fin))


def gasto_neto(uos, ini, fin):
    """Material despachado menos lo devuelto al almacén, en el período."""
    despachado = (LineaRecurso.objects
                  .filter(solicitud__uo__in=uos, solicitud__estado=SolicitudRecurso.Estado.DESPACHADA,
                          solicitud__fecha_despacho__date__range=(ini, fin))
                  .aggregate(t=Sum(IMPORTE_DESPACHADO))['t'] or CERO)
    devuelto = (Sobrante.objects
                .filter(destino=Sobrante.Destino.DEVOLUCION, linea__solicitud__uo__in=uos,
                        fecha__date__range=(ini, fin))
                .aggregate(t=Sum(IMPORTE_SOBRANTE))['t'] or CERO)
    return despachado - devuelto


def presupuesto_anual(uos, anio):
    asignado = PresupuestoAnual.objects.filter(uo__in=uos, anio=anio).aggregate(t=Sum('monto'))['t'] or CERO
    sobregiros = (Sobregiro.objects.filter(uo__in=uos, anio=anio, estado=Sobregiro.Estado.APROBADO)
                  .aggregate(t=Sum('monto_aprobado'))['t'] or CERO)
    return asignado + sobregiros


def satisfaccion(uos, ini, fin):
    """Solicitudes recibidas en el período (sin las canceladas) y cuántas ya tienen su orden cerrada."""
    recibidas = (Solicitud.objects.filter(uo__in=uos, creada__date__range=(ini, fin))
                 .exclude(estado=Solicitud.Estado.CANCELADA))
    n = recibidas.count()
    resueltas = recibidas.filter(orden__estado=Orden.Estado.CERRADA).count()
    return {'a': resueltas, 'b': n, 'pct': pct(resueltas, n)}


def asistencia(uos, ini, fin):
    qs = EstadoDiario.objects.filter(trabajador__uo__in=uos, fecha__range=(ini, fin))
    total = qs.count()
    ok = qs.filter(estado=EstadoDiario.Estado.TRABAJANDO).count()
    return round(ok * 100 / total, 1) if total else None


def disponibilidad(uos, ini, fin):
    qs = EstadoVehiculo.objects.filter(vehiculo__uo__in=uos, fecha__range=(ini, fin))
    total = qs.count()
    ok = qs.filter(estado=EstadoVehiculo.Estado.DISPONIBLE).count()
    return round(ok * 100 / total, 1) if total else None


# ---------------- indicadores (numeral 10) ----------------
def indicadores(uos, anio, mes):
    ini_m, fin_m = rango_mes(anio, mes)
    ini_a = date(anio, 1, 1)
    acciones = acciones_plan(uos, anio)

    def real(ini, fin):
        return cerradas(uos, Orden.Tipo.PREVENTIVO, ini, fin).filter(accion_plan__isnull=False).count()

    plan_mes, plan_acum = plan_en(acciones, [mes]), plan_en(acciones, range(1, mes + 1))
    real_mes, real_acum = real(ini_m, fin_m), real(ini_a, fin_m)
    presupuesto = presupuesto_anual(uos, anio)
    gastado = gasto_neto(uos, ini_a, fin_m)

    return {
        'plan_fisico': {
            'mes': {'a': real_mes, 'b': plan_mes, 'pct': pct(real_mes, plan_mes)},
            'anio': {'a': real_acum, 'b': plan_acum, 'pct': pct(real_acum, plan_acum)},
        },
        'satisfaccion': {
            'mes': satisfaccion(uos, ini_m, fin_m),
            'anio': satisfaccion(uos, ini_a, fin_m),
        },
        'gastos': {
            'gastado_mes': round(float(gasto_neto(uos, ini_m, fin_m)), 2),
            'gastado': round(float(gastado), 2),
            'presupuesto': round(float(presupuesto), 2),
            'pct': pct(gastado, presupuesto),
        },
    }


# ---------------- certificación mensual (Anexo 10) ----------------
def calcular_filas(uo, anio, mes):
    ini, fin = rango_mes(anio, mes)
    filas = {}

    def fila(inmueble_id, inmueble, grupo_id, grupo_num, grupo):
        clave = f'{inmueble_id}-{grupo_id}'
        if clave not in filas:
            filas[clave] = {'clave': clave, 'inmueble_id': inmueble_id, 'inmueble': inmueble,
                            'grupo_num': grupo_num, 'grupo': grupo, 'plan': 0, 'real': 0, 'correctivas': 0}
        return filas[clave]

    for a in acciones_plan([uo.id], anio):
        n = int(a.programacion.get(str(mes), 0))
        if n:
            fila(a.inmueble_id, a.inmueble.denominacion, a.grupo_id, a.grupo.numero, a.grupo.nombre)['plan'] += n

    preventivas = (cerradas([uo.id], Orden.Tipo.PREVENTIVO, ini, fin).filter(accion_plan__isnull=False)
                   .select_related('inmueble', 'accion_plan__grupo'))
    for o in preventivas:
        g = o.accion_plan.grupo
        fila(o.inmueble_id, o.inmueble.denominacion, g.id, g.numero, g.nombre)['real'] += 1

    correctivas = cerradas([uo.id], Orden.Tipo.CORRECTIVO, ini, fin).select_related('inmueble', 'solicitud__afectacion')
    for o in correctivas:
        g = o.solicitud.afectacion if o.solicitud_id and o.solicitud.afectacion_id else None
        if g:
            f = fila(o.inmueble_id, o.inmueble.denominacion, g.id, g.numero, g.nombre)
        else:
            f = fila(o.inmueble_id, o.inmueble.denominacion, 0, 99, GRUPO_OTRAS)
        f['correctivas'] += 1

    return sorted(filas.values(), key=lambda f: (f['inmueble'], f['grupo_num']))


def calcular_snapshot(uo, anio, mes):
    return {
        'filas': calcular_filas(uo, anio, mes),
        'indicadores': indicadores([uo.id], anio, mes),
        'generada': timezone.now().isoformat(),
    }


def filas_certificacion(cert):
    """Filas con porcentaje, total e incidencias, más el resumen. Sirve para la pantalla y el Anexo 10."""
    datos = cert.datos or {}
    inc = cert.incidencias or {}
    filas, inmuebles = [], set()
    tp = tr = tc = 0
    for f in datos.get('filas', []):
        total = f['real'] + f['correctivas']
        auto = ''
        if f['real'] > f['plan']:
            auto = 'Se ejecutaron más acciones preventivas que las planificadas este mes (incluye acciones de otros meses).'
        elif f['plan'] > f['real']:
            auto = 'Quedaron acciones preventivas planificadas sin ejecutar.'
        filas.append({**f, 'pct': pct(f['real'], f['plan']), 'total': total,
                      'incidencia': inc.get(f['clave'], ''), 'auto': auto})
        tp, tr, tc = tp + f['plan'], tr + f['real'], tc + f['correctivas']
        if total > 0:
            inmuebles.add(f['inmueble_id'])
    resumen = {'plan': tp, 'real': tr, 'pct': pct(tr, tp), 'correctivas': tc,
               'total': tr + tc, 'inmuebles': len(inmuebles)}
    return filas, resumen


# ---------------- series para los gráficos ----------------
def series(uos, periodo, anio, hoy):
    if periodo == 'semana':
        lunes = hoy - timedelta(days=hoy.weekday())
        cubos = []
        for i in range(7, -1, -1):
            ini = lunes - timedelta(weeks=i)
            cubos.append((ini, ini + timedelta(days=6), ini.strftime('%d/%m'), None))
    elif periodo == 'anio':
        cubos = [(date(y, 1, 1), date(y, 12, 31), str(y), y) for y in range(hoy.year - 4, hoy.year + 1)]
    else:
        cubos = [(*rango_mes(anio, m), MESES_ABR[m - 1], m) for m in range(1, 13)]

    acciones_del_anio = acciones_plan(uos, anio) if periodo == 'mes' else []
    claves = ('solicitudes', 'correctivas', 'preventivas', 'plan', 'gasto', 'asistencia', 'disponibilidad')
    res = {k: [] for k in claves}
    etiquetas = []

    for ini, fin, etiqueta, ref in cubos:
        etiquetas.append(etiqueta)
        if ini > hoy:  # período que todavía no llega
            for k in claves:
                res[k].append(None)
            continue
        res['solicitudes'].append(Solicitud.objects.filter(uo__in=uos, creada__date__range=(ini, fin)).count())
        res['correctivas'].append(cerradas(uos, Orden.Tipo.CORRECTIVO, ini, fin).count())
        res['preventivas'].append(cerradas(uos, Orden.Tipo.PREVENTIVO, ini, fin).count())
        if periodo == 'mes':
            res['plan'].append(plan_en(acciones_del_anio, [ref]))
        elif periodo == 'anio':
            res['plan'].append(plan_en(acciones_plan(uos, ref), range(1, 13)))
        else:
            res['plan'].append(None)
        res['gasto'].append(round(float(gasto_neto(uos, ini, fin)), 2))
        res['asistencia'].append(asistencia(uos, ini, fin))
        res['disponibilidad'].append(disponibilidad(uos, ini, fin))

    return {
        'periodo': periodo, 'anio': anio, 'etiquetas': etiquetas, 'series': res,
        'tiene_plan': any(v for v in res['plan'] if v),
    }
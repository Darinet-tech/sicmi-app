from decimal import Decimal

from accounts.models import Perfil
from ordenes.models import Orden
from .models import AccionPlan, PlanAnual
from .reglas import acciones_permitidas, proxima_firma

ROLES = dict(Perfil.Rol.choices)


def nombre(u):
    return (u.get_full_name() or u.username) if u else ''


def salida_accion(a):
    ordenes = list(a.ordenes.all())
    generadas = {}
    for o in ordenes:
        if o.estado != Orden.Estado.CANCELADA and o.mes_plan:
            generadas[o.mes_plan] = generadas.get(o.mes_plan, 0) + 1
    return {
        'id': a.id, 'inmueble': a.inmueble_id, 'inmueble_nombre': a.inmueble.denominacion,
        'grupo': a.grupo_id, 'grupo_numero': a.grupo.numero, 'grupo_nombre': a.grupo.nombre,
        'descripcion': a.descripcion, 'via': a.via, 'via_display': a.get_via_display(),
        'prioridad': a.prioridad, 'es_compleja': a.es_compleja,
        'programacion': a.programacion, 'cantidad': a.cantidad, 'valor_estimado': a.valor_estimado,
        'tiene_tt': hasattr(a, 'tarea_tecnica'), 'tiene_croquis': hasattr(a, 'croquis'),
        'generadas': generadas,
        'ordenes': [{'id': o.id, 'codigo': o.codigo, 'mes': o.mes_plan, 'estado': o.estado,
                     'estado_display': o.get_estado_display()} for o in ordenes],
    }


def salida_plan(plan, user, detalle=True):
    propias = [a for a in plan.acciones.all() if a.via == AccionPlan.Via.PROPIOS]
    datos = {
        'id': plan.id, 'anio': plan.anio, 'uo_acronimo': plan.uo.acronimo,
        'estado': plan.estado, 'estado_display': plan.get_estado_display(),
        'num_obras': len(propias),
        'total_acciones': sum(a.cantidad for a in propias),
        'valor_mcup': sum((a.valor_estimado for a in propias), Decimal('0')),
    }
    if not detalle:
        return datos

    from recursos.models import PresupuestoAnual
    pres = PresupuestoAnual.objects.filter(uo=plan.uo, anio=plan.anio).first()
    por_mes = {m: sum(a.programacion.get(str(m), 0) for a in propias) for m in range(1, 13)}
    datos.update({
        'elaborado_por': nombre(plan.elaborado_por), 'motivo_devolucion': plan.motivo_devolucion,
        'presupuesto_mcup': (pres.monto / 1000) if pres else None,
        'por_mes': por_mes,
        'firmas': [{'rol': f.rol, 'rol_display': ROLES.get(f.rol, f.rol),
                    'usuario': nombre(f.usuario), 'fecha': f.fecha} for f in plan.firmas.all()],
        'proxima_firma': proxima_firma(plan) if plan.estado == PlanAnual.Estado.EN_FIRMAS else None,
        'acciones_permitidas': acciones_permitidas(plan, user),
        'acciones': [salida_accion(a) for a in plan.acciones.all()],
        'historial': [{'usuario': nombre(h.usuario), 'comentario': h.comentario, 'fecha': h.fecha}
                      for h in plan.historial.all()],
    })
    return datos


def salida_tt(tt, user):
    if tt is None:
        p = user.perfil
        return {'existe': False, 'descripcion_general': '', 'trabajos': [],
                'elaborado_nombre': nombre(user), 'elaborado_cargo': p.cargo}
    return {'existe': True, 'descripcion_general': tt.descripcion_general, 'trabajos': tt.trabajos,
            'elaborado_nombre': tt.elaborado_nombre, 'elaborado_cargo': tt.elaborado_cargo}


def salida_croquis(c):
    if c is None:
        return {'existe': False}
    return {
        'existe': True, 'url': c.imagen.url if c.imagen else None,
        'plano_no': c.plano_no, 'escala': c.escala, 'fecha': c.fecha, 'proyecto': c.proyecto,
        'plano': c.plano, 'elaborado': c.elaborado, 'proyectado': c.proyectado, 'aprobado': c.aprobado,
        'actualizado': c.actualizado,
    }
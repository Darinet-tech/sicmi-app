from datetime import datetime
from decimal import Decimal
from itertools import groupby

from django.utils import timezone

from recursos.models import SolicitudRecurso
from recursos.servicios import materiales_de_orden
from .render import Documento

S = SolicitudRecurso.Estado


def f_fecha(d):
    if not d:
        return ''
    if isinstance(d, datetime):
        d = timezone.localtime(d)
    return d.strftime('%d/%m/%Y')


def nombre(u):
    return (u.get_full_name() or u.username) if u else ''


def cargo(u):
    p = getattr(u, 'perfil', None) if u else None
    return p.cargo if p else ''


# ---------- Anexo 1 ----------
def anexo1(s):
    doc = Documento('SOLICITUD DEL SERVICIO DE MANTENIMIENTO', 'ANEXO 1 · REG.1-PE-SG-020/18',
                    f'Anexo1-Solicitud-{s.id}')
    afectacion = s.afectacion.nombre if s.afectacion_id else s.otra_afectacion
    doc.campos([
        ('No. de solicitud', f'#{s.id}'),
        ('Unidad Organizativa', f'{s.uo.nombre} ({s.uo.acronimo})'),
        ('Nombre del Inmueble', s.inmueble.denominacion),
        ('Área solicitante', s.area_solicitante.nombre),
        ('Centro de Costo', str(s.centro_costo)),
        ('Local donde ocurre la incidencia', s.local.nombre),
        ('Afectación', afectacion),
    ], cols=1)
    doc.texto('Descripción de las afectaciones', s.descripcion, alto=55)
    doc.campos([
        ('Elaborado por (nombre y apellidos)', nombre(s.solicitante)),
        ('Cargo', cargo(s.solicitante)),
        ('Fecha', f_fecha(s.creada)),
    ], cols=1)
    doc.firmas([('Firma del solicitante', nombre(s.solicitante), f_fecha(s.creada))])
    return doc


# ---------- Anexo 2 ----------
def anexo2(uo, anio, ordenes):
    doc = Documento('REGISTRO ÚNICO DE ÓRDENES DE TRABAJO DE MANTENIMIENTO DE INMUEBLES POR MEDIOS PROPIOS',
                    'ANEXO 2 · REG.2-PE-SG-020/18',
                    f'Anexo2-Registro-{uo.acronimo if uo else "TODAS"}-{anio}', horizontal=True)
    doc.campos([
        ('Unidad Organizativa', f'{uo.nombre} ({uo.acronimo})' if uo else 'Todas las unidades'),
        ('Año', str(anio)),
    ], cols=2)
    filas = []
    for o in ordenes:
        obs = []
        if o.estado == 'CANCELADA':
            h = next((x for x in reversed(list(o.historial.all())) if x.estado_nuevo == 'CANCELADA'), None)
            obs.append('Cancelada' + (f': {h.comentario}' if h and h.comentario else ''))
        vales = [s.vale_numero for s in o.solicitudes_recursos.all() if s.estado == S.DESPACHADA and s.vale_numero]
        if vales:
            obs.append('Vales: ' + ', '.join(vales))
        filas.append((
            o.codigo if uo else f'{o.uo.acronimo} {o.codigo}',
            o.inmueble.denominacion, str(o.centro_costo),
            'X' if o.tipo == 'MC' else '', 'X' if o.tipo == 'MP' else '',
            f_fecha(o.creada), f_fecha(o.fecha_cierre), '. '.join(obs),
        ))
    doc.tabla(None, ['No.', 'Denominación del inmueble', 'Centro de costo', 'MC', 'MP', 'Inicio', 'Cierre', 'Observaciones'],
              filas, pesos=[1.3, 4, 2.2, 0.6, 0.6, 1.3, 1.3, 4.5], min_filas=12)
    return doc


# ---------- Anexo 3 ----------
def anexo3(sol, tipo):
    salida = tipo == 'salida'
    orden, uo = sol.orden, sol.uo
    doc = Documento('MODELO SOLICITUD DE RECURSOS', 'ANEXO 3 · PE-SG-020/18',
                    f'Anexo3-{"Salida" if salida else "Devolucion"}-{sol.codigo}')
    doc.marcas('Tipo', [('Solicitud de Mat. (Salida)', salida), ('Devolución de Mat.', not salida),
                        ('Transf. e/ Alm.', False)])

    lineas = list(sol.lineas.all())
    devueltas = [x for l in lineas for x in l.sobrantes.all() if x.destino == 'DEVOLUCION']
    if salida:
        vale = sol.vale_numero
    else:
        vale = ', '.join(sorted({x.vale_devolucion for x in devueltas if x.vale_devolucion}))

    doc.campos([
        ('Fecha', f_fecha(timezone.localdate())),
        ('No. Consecutivo', sol.codigo),
        ('Nombre y Código Entidad', f'{uo.nombre} ({uo.acronimo})'),
        ('Orden de trabajo', orden.codigo),
        ('Almacén al que se solicita' if salida else 'Almacén al que se devuelve', str(sol.almacen)),
        ('No. vale de salida' if salida else 'No. vale de devolución', vale),
        ('Nombre y Código del Área', orden.area_solicitante.nombre),
        ('Centro de Costo', str(orden.centro_costo)),
    ], cols=2)

    filas = []
    if salida:
        despachada = sol.estado == S.DESPACHADA
        for l in lineas:
            filas.append((l.material.codigo_sap, l.material.descripcion, l.material.unidad_medida,
                          l.cantidad_despachada if despachada else l.cantidad))
    elif devueltas:
        for x in devueltas:
            m = x.linea.material
            filas.append((m.codigo_sap, m.descripcion, m.unidad_medida, x.cantidad))
    else:  # formato para llenar a mano
        for l in lineas:
            filas.append((l.material.codigo_sap, l.material.descripcion, l.material.unidad_medida, ''))
    doc.tabla(None, ['Código SAP-MM', 'Descripción SAP-MM del producto', 'U/M', 'Cantidad'], filas,
              formatos=['texto', 'texto', 'texto', 'cant'], pesos=[2, 6, 1, 1.5], min_filas=8)
    doc.campos([('Destino', f'{orden.inmueble.denominacion} · Orden de trabajo {orden.codigo}')], cols=1)

    if salida:
        doc.firmas([
            ('Solicitado por', nombre(sol.solicitada_por), f_fecha(sol.creada)),
            ('Autorizado por', nombre(sol.autorizada_por), f_fecha(sol.fecha_autorizacion)),
            ('Recibido por', nombre(sol.despachada_por), f_fecha(sol.fecha_despacho)),
        ])
    else:
        quien = devueltas[0] if devueltas else None
        doc.firmas([
            ('Devuelto por', nombre(quien.registrado_por) if quien else '', f_fecha(quien.fecha) if quien else ''),
            ('Autorizado por', '', ''),
            ('Recibido por (almacén)', '', ''),
        ])
    return doc


# ---------- Anexos 4 y 5 ----------
def anexo4(s):
    doc = Documento('SOLICITUD DE SOBREGIRO', 'ANEXO 4 · PE-SG-020/18', f'Anexo4-Sobregiro-{s.uo.acronimo}-{s.id}')
    doc.parrafo('Solicitud de sobregiro por gastos de mantenimiento a inmuebles por medios propios.')
    doc.campos([
        ('Fecha', f_fecha(s.creado)),
        ('A', 'Director Central - División de Logística y Servicios'),
        ('Asunto de referencia', 'Solicitud de aprobación de sobregiro.'),
    ], cols=1)
    doc.parrafo('Requerimos su respuesta en relación a la disponibilidad de financiamiento para el '
                'mantenimiento a inmuebles por medios propios.')
    doc.tabla(None, ['Concepto', 'CUP'], [
        ('Financiamiento asignado en el año (CUP)', s.financiamiento_asignado),
        ('Real gastado hasta la fecha (CUP)', s.real_gastado),
        ('Sobregiro solicitado en el año (CUP)', s.monto_solicitado),
    ], formatos=['texto', 'dinero'], pesos=[4, 1.5])
    doc.texto('Fundamentación', s.fundamentacion, alto=30)
    doc.parrafo('Atentamente,')
    doc.firmas([('Director Unidad Organizativa', nombre(s.solicitado_por), f_fecha(s.creado))])
    doc.campos([('c.c.', 'Director Dirección de Servicios Generales')], cols=1)
    return doc


def anexo5(s):
    doc = Documento('APROBACIÓN DE SOBREGIRO', 'ANEXO 5 · PE-SG-020/18', f'Anexo5-Aprobacion-{s.uo.acronimo}-{s.id}')
    doc.parrafo('Aprobación de sobregiro por gastos de mantenimiento a inmuebles por medios propios.')
    doc.campos([
        ('Fecha', f_fecha(s.resuelto)),
        ('A', f'Director - {s.uo.nombre} ({s.uo.acronimo})'),
        ('Asunto de referencia', 'Aprobación de sobregiro.'),
    ], cols=1)
    doc.parrafo('Por la presente, los que suscriben certifican que se aprueba la ejecución de sobregiro del '
                'plan para gastos de mantenimiento a inmuebles con medios propios.')
    doc.tabla(None, ['Concepto', 'CUP'], [('Financiamiento aprobado (CUP)', s.monto_aprobado)],
              formatos=['texto', 'dinero'], pesos=[4, 1.5])
    doc.texto('Fundamentación', s.respuesta or s.fundamentacion, alto=30)
    doc.parrafo('Atentamente,')
    doc.firmas([
        ('Confeccionado por: Jefe Dpto. de Inmobiliaria', '', ''),
        ('Revisado por: Director de Servicios Generales', '', ''),
        ('Aprobado por: Director Central', nombre(s.resuelto_por), f_fecha(s.resuelto)),
    ])
    return doc


# ---------- Anexo 6 ----------
def anexo6(o):
    doc = Documento('ORDEN DE TRABAJO PARA LA ACTIVIDAD DE MANTENIMIENTO DE INMUEBLES',
                    'ANEXO 6 · REG.3-PE-SG-020/18', f'Anexo6-Orden-{o.codigo}')
    doc.campos([('No. orden de trabajo', o.codigo), ('Estado', o.get_estado_display())], cols=2)
    doc.marcas('Mantenimiento', [('Correctivo', o.tipo == 'MC'), ('Preventivo', o.tipo == 'MP')])
    doc.campos([
        ('Denominación del inmueble', o.inmueble.denominacion),
        ('Área solicitante', o.area_solicitante.nombre),
        ('Centro de costo', str(o.centro_costo)),
        ('Local', o.local.nombre if o.local else ''),
        ('Fecha de solicitud', f_fecha(o.fecha_solicitud)),
        ('Fecha de cierre', f_fecha(o.fecha_cierre)),
    ], cols=2)
    brigadas = '; '.join(
        f'{b.brigada.nombre} ({f_fecha(b.desde)} - {f_fecha(b.hasta) or "vigente"})' for b in o.brigadas.all())
    doc.campos([
        ('Afectación', o.afectacion),
        ('Brigada(s)', brigadas),
        ('Vehículo', str(o.vehiculo) if o.vehiculo else ''),
        ('Inspección realizada por', o.inspeccion_por),
    ], cols=1)
    doc.texto('Descripción de los trabajos realizados', o.descripcion_trabajos, alto=22)
    doc.tabla('PARTICIPANTES', ['Trabajador', 'Desde', 'Hasta', 'Motivo'], [
        (p.trabajador.nombre, f_fecha(p.desde), f_fecha(p.hasta) or 'vigente', p.motivo)
        for p in o.participantes.all()
    ], pesos=[4, 1.3, 1.3, 4], min_filas=3)

    materiales = materiales_de_orden(o)
    filas = [(m['vale'],
              f"{m['codigo']} - {m['descripcion']}" + (f" ({m['origen']})" if m['origen'] else ''),
              m['um'], m['cantidad'], m['precio'], m['importe']) for m in materiales]
    doc.tabla('CONTROL DE LOS MATERIALES UTILIZADOS',
              ['No. vale', 'Descripción del material', 'U/M', 'Cantidad', 'Precio', 'Importe'], filas,
              formatos=['texto', 'texto', 'texto', 'cant', 'dinero', 'dinero'], pesos=[1.3, 5, 0.9, 1.2, 1.2, 1.4],
              pie=('VALOR TOTAL (CUP)', sum((m['importe'] for m in materiales), 0)), min_filas=4)
    doc.texto('Incidencias a reportar', o.incidencias, alto=14)

    firmadas = {f.rol: f for f in o.firmas.all()}

    def firma(rol, titulo, por_defecto=''):
        f = firmadas.get(rol)
        return (titulo, nombre(f.usuario) if f else por_defecto, f_fecha(f.fecha) if f else '')

    doc.firmas([
        firma('CLIENTE', 'CLIENTE', nombre(o.cliente)),
        firma('JEFE_BRIGADA', 'J. BRIGADA DE MTTO'),
        firma('JEFE_GRUPO', 'J. GRUPO SERVICIOS'),
        firma('ESPECIALISTA', 'ESPECIALISTA'),
    ])
    return doc


# ---------- Anexo 7 ----------
def anexo7(a):
    tt = a.tarea_tecnica
    uo = a.plan.uo
    doc = Documento('TAREA TÉCNICA', 'ANEXO 7 · PE-SG-020/18', f'Anexo7-TareaTecnica-{uo.acronimo}-{a.id}')
    doc.campos([
        ('Denominación', a.inmueble.denominacion),
        ('Dirección', a.inmueble.direccion),
        ('Obra', f'{a.grupo.numero}. {a.grupo.nombre} · Plan Anual {a.plan.anio}'),
    ], cols=1)
    doc.texto('Descripción general del inmueble u objeto de obra', tt.descripcion_general, alto=28)
    filas = [(i, t.get('desperfecto', ''), t.get('trabajo', ''), t.get('um', ''), t.get('cantidad', ''))
             for i, t in enumerate(tt.trabajos, start=1)]
    doc.tabla('TRABAJOS CONSTRUCTIVOS A REALIZAR',
              ['No', 'Desperfectos / Ubicación y tipo', 'Trabajos a realizar', 'UM', 'Cantidad'],
              filas, pesos=[0.6, 4, 5, 0.9, 1.2], min_filas=8)
    doc.campos([
        ('Nombre y apellidos', tt.elaborado_nombre),
        ('Cargo', tt.elaborado_cargo),
        ('Unidad Organizativa', f'{uo.nombre} ({uo.acronimo})'),
    ], cols=1)
    return doc


# ---------- Anexo 8 ----------
def anexo8(c):
    a = c.accion
    uo = a.plan.uo
    doc = Documento('PROFORMA DE CROQUIS O PLANO DE OBRA', 'ANEXO 8 · PE-SG-020/18',
                    f'Anexo8-Croquis-{uo.acronimo}-{a.id}', horizontal=True)
    doc.imagen(c.imagen.path, alto_mm=98)
    doc.campos([
        ('Plano No.', c.plano_no), ('Escala', c.escala), ('Fecha', f_fecha(c.fecha)), ('Proyecto', c.proyecto),
        ('Elaborado', c.elaborado), ('Proyectado', c.proyectado), ('Aprobado', c.aprobado),
        ('Plano', c.plano or f'{a.grupo.nombre} · {a.inmueble.denominacion}'),
    ], cols=4)
    doc.campos([('Unidad Organizativa', f'{uo.nombre} ({uo.acronimo})')], cols=1)
    return doc


# ---------- Anexo 9 ----------
def anexo9(plan):
    doc = Documento('PLAN ANUAL DE MANTENIMIENTO PREVENTIVO CON MEDIOS PROPIOS',
                    'ANEXO 9 · REG.4-PE-SG-020/18',
                    f'Anexo9-Plan-{plan.uo.acronimo}-{plan.anio}', horizontal=True)
    doc.campos([
        ('Unidad Organizativa', f'{plan.uo.nombre} ({plan.uo.acronimo})'),
        ('Año', str(plan.anio)),
    ], cols=2)

    acciones = sorted(
        (a for a in plan.acciones.select_related('inmueble', 'grupo') if a.via == 'PROPIOS'),
        key=lambda a: (a.inmueble.denominacion, a.grupo.numero))

    def texto_meses(valores):
        return [str(n) if n else '' for n in valores]

    filas, resaltar = [], set()
    total_meses, total_cant, total_valor = [0] * 12, 0, Decimal('0')
    for _, grupo in groupby(acciones, key=lambda a: a.inmueble_id):
        grupo = list(grupo)
        sub_meses, sub_cant, sub_valor = [0] * 12, 0, Decimal('0')
        for a in grupo:
            marcas = []
            for m in range(1, 13):
                n = a.programacion.get(str(m), 0)
                marcas.append('' if not n else ('X' if n == 1 else f'X{n}'))
                sub_meses[m - 1] += n
            sub_cant += a.cantidad
            sub_valor += a.valor_estimado
            filas.append((a.inmueble.denominacion, f'Mantenimiento y reparación menor de {a.grupo.nombre}',
                          a.cantidad, *marcas, a.valor_estimado))
        if len(grupo) > 1:  # total por inmueble
            resaltar.add(len(filas))
            filas.append((f'Total {grupo[0].inmueble.denominacion}', '', sub_cant,
                          *texto_meses(sub_meses), sub_valor))
        total_meses = [x + y for x, y in zip(total_meses, sub_meses)]
        total_cant += sub_cant
        total_valor += sub_valor
    resaltar.add(len(filas))
    filas.append(('TOTALES', '', total_cant, *texto_meses(total_meses), total_valor))

    doc.tabla(None,
              ['Denominación del inmueble', 'Descripción de las acciones', 'Cantidad de acciones',
               'E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D', 'Valor estimado (MCUP)'],
              filas, formatos=['texto', 'texto', 'cant'] + ['texto'] * 12 + ['dinero'],
              pesos=[3.2, 5.5, 1.1] + [0.6] * 12 + [1.5], resaltar=resaltar)
    doc.parrafo('X = acción planificada en el mes (un número indica varias acciones en el mismo mes). '
                'El valor se expresa en miles de CUP.')

    firmadas = {x.rol: x for x in plan.firmas.select_related('usuario')}

    def firma(rol, titulo):
        x = firmadas.get(rol)
        return (titulo, nombre(x.usuario) if x else '', f_fecha(x.fecha) if x else '')

    doc.firmas([
        firma('ESPECIALISTA', 'Confeccionado por: Especialista Obras de Ingenierías'),
        firma('JEFE_GRUPO', 'Revisado por: Jefe Grupo de Servicios'),
        firma('JEFE_LOGISTICA', 'Revisado por: Jefe Dpto. Logística y Servicios'),
        firma('DIRECTOR_UO', 'Aprobado por: Director Unidad'),
    ])
    return doc

# ---------- Anexo 10 ----------
def anexo10(cert):
    from reportes.calculos import MESES, filas_certificacion

    filas, resumen = filas_certificacion(cert)
    uo = cert.uo
    doc = Documento('CERTIFICACIÓN MENSUAL DE MANTENIMIENTO DE INMUEBLES POR MEDIOS PROPIOS EN FÍSICO',
                    'ANEXO 10 · REG.5-PE-SG-020/18',
                    f'Anexo10-Certificacion-{uo.acronimo}-{cert.anio}-{cert.mes:02d}', horizontal=True)
    doc.campos([
        ('Unidad Organizativa', f'{uo.nombre} ({uo.acronimo})'),
        ('Mes', MESES[cert.mes - 1]),
        ('Año', str(cert.anio)),
    ], cols=3)

    def texto_pct(v):
        return '' if v is None else f'{v} %'

    filas_doc = []
    for f in filas:
        incidencias = ' '.join(x for x in (f['incidencia'], f['auto']) if x)
        accion = f['grupo'] if f['grupo_num'] == 99 else f"Mantenimiento y reparación menor de {f['grupo']}"
        filas_doc.append((f['inmueble'], accion, f['plan'], f['real'], texto_pct(f['pct']),
                          f['correctivas'], f['total'], incidencias))
    resaltar = {len(filas_doc)}
    filas_doc.append(('Resumen total de acciones', '', resumen['plan'], resumen['real'],
                      texto_pct(resumen['pct']), resumen['correctivas'], resumen['total'], ''))
    resaltar.add(len(filas_doc))
    filas_doc.append(('Cantidad de inmuebles donde se ejecutaron acciones constructivas', '', '', '', '', '',
                      resumen['inmuebles'], ''))

    doc.tabla(None,
              ['Denominación del inmueble', 'Resumen de acciones', 'Prev. plan', 'Prev. real', '% cumpl.',
               'Correctivas', 'Total', 'Incidencias'],
              filas_doc,
              formatos=['texto', 'texto', 'cant', 'cant', 'texto', 'cant', 'cant', 'texto'],
              pesos=[3, 4.5, 0.9, 0.9, 0.9, 1.2, 0.9, 4.2], resaltar=resaltar)

    firmadas = {x.rol: x for x in cert.firmas.select_related('usuario')}

    def firma(rol, titulo):
        x = firmadas.get(rol)
        return (titulo, nombre(x.usuario) if x else '', f_fecha(x.fecha) if x else '')

    doc.firmas([
        firma('ESPECIALISTA', 'Elaborado por: Especialista en Obras de Ingenierías'),
        firma('JEFE_GRUPO', 'Revisado por: Jefe Grupo de Servicios'),
        firma('JEFE_LOGISTICA', 'Aprobado por: Jefe Dpto. Logística y Servicios'),
    ])
    return doc
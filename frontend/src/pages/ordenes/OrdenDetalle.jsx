import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FileCheck2, CheckCircle2, Circle } from 'lucide-react'
import api, { textoError } from '../../api'
import PaginaModulo from '../../PaginaModulo'
import { ESTADOS_TRABAJADOR } from '../personal/estados'
import { CADENA_FIRMAS } from './estados'
import { EtiquetaOrden } from './OrdenesLista'

const fecha = (f) => (f ? new Date(f + 'T00:00:00').toLocaleDateString('es') : '—')

export default function OrdenDetalle() {
  const { id } = useParams()
  const [o, setO] = useState(null)
  const [error, setError] = useState('')
  const [avisos, setAvisos] = useState([])
  const [ocupado, setOcupado] = useState(false)

  const [edit, setEdit] = useState({ descripcion_trabajos: '', incidencias: '', vehiculo: '' })
  const [trabajadores, setTrabajadores] = useState([])
  const [brigadas, setBrigadas] = useState([])
  const [vehiculos, setVehiculos] = useState([])
  const [nuevoPart, setNuevoPart] = useState({ trabajador: '', motivo: '' })
  const [nuevaBrig, setNuevaBrig] = useState({ brigada: '', reemplazar: false })
  const [noConforme, setNoConforme] = useState(false)
  const [comentario, setComentario] = useState('')

  useEffect(() => {
    api
      .get(`ordenes/${id}/`)
      .then((r) => {
        setO(r.data)
        setEdit({
          descripcion_trabajos: r.data.descripcion_trabajos,
          incidencias: r.data.incidencias,
          vehiculo: r.data.vehiculo || '',
        })
      })
      .catch((e) => setError(textoError(e)))
  }, [id])

  const acc = o?.acciones || []
  const editable = acc.includes('editar')

  // Catálogos para los desplegables (solo si la orden se puede editar)
  useEffect(() => {
    if (!editable) return
    Promise.all([api.get('trabajadores/'), api.get('brigadas/'), api.get('vehiculos/')])
      .then(([t, b, v]) => {
        setTrabajadores(t.data.filter((x) => x.activo))
        setBrigadas(b.data.filter((x) => x.activa))
        setVehiculos(v.data.filter((x) => x.activo))
      })
      .catch((e) => setError(textoError(e)))
  }, [editable])

  // Ejecuta una acción de la orden y refresca los datos
  async function llamar(accion, cuerpo = {}, metodo = 'post') {
    setError('')
    setAvisos([])
    setOcupado(true)
    try {
      const r = await api[metodo](`ordenes/${id}/${accion}/`, cuerpo)
      const { avisos: av, ...datos } = r.data
      setO(datos)
      if (av?.length) setAvisos(av)
      return true
    } catch (e) {
      setError(textoError(e))
      return false
    } finally {
      setOcupado(false)
    }
  }

  const cuerpoEdicion = () => ({
    descripcion_trabajos: edit.descripcion_trabajos,
    incidencias: edit.incidencias,
    vehiculo: edit.vehiculo ? Number(edit.vehiculo) : null,
  })

  const guardar = () => llamar('editar', cuerpoEdicion(), 'patch')

  async function entregar() {
    // Guarda primero lo escrito, para no perderlo
    if (await llamar('editar', cuerpoEdicion(), 'patch')) await llamar('entregar')
  }

  async function agregarParticipante() {
    if (!nuevoPart.trabajador) return
    const ok = await llamar('agregar_participante', {
      trabajador: Number(nuevoPart.trabajador), motivo: nuevoPart.motivo,
    })
    if (ok) setNuevoPart({ trabajador: '', motivo: '' })
  }

  async function agregarBrigada() {
    if (!nuevaBrig.brigada) return
    const ok = await llamar('agregar_brigada', {
      brigada: Number(nuevaBrig.brigada), reemplazar: nuevaBrig.reemplazar,
    })
    if (ok) setNuevaBrig({ brigada: '', reemplazar: false })
  }

  async function conformidad(conforme) {
    const ok = await llamar('conformidad', { conforme, comentario })
    if (ok) {
      setNoConforme(false)
      setComentario('')
    }
  }

  function cancelar() {
    const motivo = window.prompt('Motivo de la cancelación de la orden:')
    if (motivo && motivo.trim()) llamar('cancelar', { comentario: motivo })
  }

  if (!o) return error ? <div className="error">{error}</div> : <p>Cargando...</p>

  const vigentes = o.participantes.filter((p) => p.vigente)
  const disponibles = trabajadores.filter((t) => !vigentes.some((p) => p.trabajador === t.id))
  const brigadasLibres = brigadas.filter((b) => !o.brigadas.some((x) => x.vigente && x.brigada === b.id))
  const hayBrigadaVigente = o.brigadas.some((b) => b.vigente)

  return (
    <PaginaModulo
      icono={FileCheck2}
      titulo={`Orden de trabajo ${o.codigo}`}
      descripcion={`${o.tipo_display} · ${o.uo_acronimo}`}
      acciones={<Link className="btn btn-gris" to="/ordenes">← Volver</Link>}
    >
      <div className="barra" style={{ marginTop: '-0.5rem' }}>
        <EtiquetaOrden estado={o.estado} />
        {o.solicitud && <Link to={`/solicitudes/${o.solicitud}`}>Ver solicitud origen</Link>}
      </div>

      {error && <div className="error">{error}</div>}
      {avisos.map((a, i) => <div key={i} className="aviso">{a}</div>)}

      <div className="tarjeta">
        <h3>Datos de la orden</h3>
        <dl className="datos">
          <dt>Inmueble</dt><dd>{o.inmueble_nombre}</dd>
          <dt>Local</dt><dd>{o.local_nombre || '—'}</dd>
          <dt>Área solicitante</dt><dd>{o.area_nombre}</dd>
          <dt>Centro de costo</dt><dd>{o.centro_costo_nombre}</dd>
          <dt>Cliente</dt><dd>{o.cliente_nombre}</dd>
          <dt>Afectación</dt><dd>{o.afectacion}</dd>
          <dt>Descripción del cliente</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{o.descripcion_solicitud}</dd>
          <dt>Inspección realizada por</dt><dd>{o.inspeccion_por || '—'}</dd>
          <dt>Fecha de solicitud</dt><dd>{fecha(o.fecha_solicitud)}</dd>
          <dt>Fecha de cierre</dt><dd>{fecha(o.fecha_cierre)}</dd>
        </dl>
      </div>

      <div className="tarjeta">
        <h3>Trabajos realizados</h3>
        {editable ? (
          <>
            <label style={{ marginTop: 0 }}>Descripción de los trabajos realizados</label>
            <textarea value={edit.descripcion_trabajos}
              onChange={(e) => setEdit({ ...edit, descripcion_trabajos: e.target.value })} />
            <label>Incidencias a reportar</label>
            <textarea style={{ minHeight: 70 }} value={edit.incidencias}
              onChange={(e) => setEdit({ ...edit, incidencias: e.target.value })} />
            <label>Vehículo asignado</label>
            <select value={edit.vehiculo} onChange={(e) => setEdit({ ...edit, vehiculo: e.target.value })}>
              <option value="">-- Sin vehículo --</option>
              {vehiculos.map((v) => <option key={v.id} value={v.id}>{v.chapa} {v.tipo}</option>)}
            </select>
            <div className="fila-botones">
              <button className="btn btn-verde" onClick={guardar} disabled={ocupado}>Guardar</button>
            </div>
          </>
        ) : (
          <dl className="datos">
            <dt>Trabajos</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{o.descripcion_trabajos || '—'}</dd>
            <dt>Incidencias</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{o.incidencias || '—'}</dd>
            <dt>Vehículo</dt><dd>{o.vehiculo_texto || '—'}</dd>
          </dl>
        )}
      </div>

      <div className="tarjeta">
        <h3>Brigadas</h3>
        {o.brigadas.length === 0 ? (
          <p style={{ color: 'var(--gris)' }}>Sin brigada asignada.</p>
        ) : (
          <ul className="miembros">
            {o.brigadas.map((b, i) => (
              <li key={i}>
                <span>
                  {b.nombre}
                  <small>{fecha(b.desde)} → {b.vigente ? 'vigente' : fecha(b.hasta)}</small>
                </span>
                {editable && b.vigente && (
                  <button className="btn btn-gris" disabled={ocupado}
                    onClick={() => llamar('retirar_brigada', { brigada: b.brigada })}>Retirar</button>
                )}
              </li>
            ))}
          </ul>
        )}
        {editable && (
          <>
            <div className="agregar-miembro">
              <select value={nuevaBrig.brigada} onChange={(e) => setNuevaBrig({ ...nuevaBrig, brigada: e.target.value })}>
                <option value="">-- Agregar brigada --</option>
                {brigadasLibres.map((b) => <option key={b.id} value={b.id}>{b.nombre}</option>)}
              </select>
              <button className="btn btn-verde" onClick={agregarBrigada} disabled={ocupado}>Agregar</button>
            </div>
            {hayBrigadaVigente && (
              <label style={{ fontWeight: 400 }}>
                <input type="checkbox" checked={nuevaBrig.reemplazar}
                  onChange={(e) => setNuevaBrig({ ...nuevaBrig, reemplazar: e.target.checked })} />{' '}
                Reemplaza a la brigada actual (esta queda registrada con su fecha de fin)
              </label>
            )}
          </>
        )}
      </div>

      <div className="tarjeta">
        <h3>Participantes</h3>
        {o.participantes.length === 0 ? (
          <p style={{ color: 'var(--gris)' }}>Todavía no hay participantes.</p>
        ) : (
          <div className="tabla-wrap">
            <table>
              <thead>
                <tr><th>Trabajador</th><th>Desde</th><th>Hasta</th><th>Hoy</th><th>Motivo</th>{editable && <th />}</tr>
              </thead>
              <tbody>
                {o.participantes.map((p, i) => (
                  <tr key={i} className={p.alerta ? 'fila-alerta' : ''} style={{ opacity: p.vigente ? 1 : 0.6 }}>
                    <td>{p.nombre}</td>
                    <td>{fecha(p.desde)}</td>
                    <td>{p.vigente ? 'vigente' : fecha(p.hasta)}</td>
                    <td>
                      {p.vigente && (
                        <span className={`etiqueta t-${p.estado_hoy}`}>{ESTADOS_TRABAJADOR[p.estado_hoy]}</span>
                      )}
                    </td>
                    <td>{p.motivo}</td>
                    {editable && (
                      <td>
                        {p.vigente && (
                          <button className="btn btn-gris" disabled={ocupado}
                            onClick={() => llamar('retirar_participante', { trabajador: p.trabajador })}>
                            Retirar
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {o.participantes.some((p) => p.alerta) && (
          <div className="aviso">
            Hay participantes que hoy no figuran como Trabajando. Agregue un reemplazo: quien se retira
            queda registrado en la orden con su fecha de fin.
          </div>
        )}
        {editable && (
          <div className="dos-columnas" style={{ marginTop: '1rem' }}>
            <select value={nuevoPart.trabajador} onChange={(e) => setNuevoPart({ ...nuevoPart, trabajador: e.target.value })}>
              <option value="">-- Agregar participante --</option>
              {disponibles.map((t) => <option key={t.id} value={t.id}>{t.codigo} · {t.nombre}</option>)}
            </select>
            <div className="agregar-miembro" style={{ marginTop: 0 }}>
              <input type="text" placeholder="Motivo (ej. reemplazo de ...)" value={nuevoPart.motivo}
                onChange={(e) => setNuevoPart({ ...nuevoPart, motivo: e.target.value })} />
              <button className="btn btn-verde" onClick={agregarParticipante} disabled={ocupado}>Agregar</button>
            </div>
          </div>
        )}
      </div>

      <div className="tarjeta">
        <h3>Firmas</h3>
        <div className="cadena-firmas">
          {CADENA_FIRMAS.map(([rol, texto]) => {
            const f = o.firmas.find((x) => x.rol === rol)
            return (
              <div key={rol} className={`firma ${f ? 'hecha' : ''}`}>
                {f ? <CheckCircle2 size={22} /> : <Circle size={22} />}
                <div>
                  <b>{texto}</b>
                  <small>{f ? `${f.usuario} · ${new Date(f.fecha).toLocaleString('es')}` : 'Pendiente'}</small>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {(acc.some((a) => a !== 'editar')) && (
        <div className="tarjeta">
          <h3>Acciones</h3>
          {!noConforme && (
            <div className="fila-botones" style={{ marginTop: 0 }}>
              {acc.includes('iniciar') && (
                <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('iniciar')}>
                  Iniciar ejecución
                </button>
              )}
              {acc.includes('entregar') && (
                <button className="btn btn-verde" disabled={ocupado} onClick={entregar}>
                  Entregar trabajo al cliente
                </button>
              )}
              {acc.includes('conformidad') && (
                <>
                  <button className="btn btn-verde" disabled={ocupado} onClick={() => conformidad(true)}>
                    Estoy conforme con el trabajo
                  </button>
                  <button className="btn btn-gris" onClick={() => setNoConforme(true)}>No estoy conforme</button>
                </>
              )}
              {acc.includes('firmar') && (
                <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('firmar')}>
                  Firmar la orden
                </button>
              )}
              {acc.includes('cancelar') && (
                <button className="btn btn-peligro" disabled={ocupado} onClick={cancelar}>Cancelar orden</button>
              )}
            </div>
          )}
          {noConforme && (
            <>
              <label style={{ marginTop: 0 }}>Motivo de la no conformidad (obligatorio)</label>
              <textarea value={comentario} onChange={(e) => setComentario(e.target.value)} />
              <div className="fila-botones">
                <button className="btn btn-verde" disabled={ocupado} onClick={() => conformidad(false)}>Enviar</button>
                <button className="btn btn-gris" onClick={() => setNoConforme(false)}>Volver</button>
              </div>
            </>
          )}
        </div>
      )}

      <div className="tarjeta">
        <h3>Historial</h3>
        <ul className="historial">
          {o.historial.map((h, i) => (
            <li key={i}>
              <strong>{h.estado_anterior && h.estado_anterior !== h.estado_nuevo ? `${h.estado_anterior} → ` : ''}{h.estado_nuevo}</strong>
              <br />
              <small>{h.usuario} · {new Date(h.fecha).toLocaleString('es')}</small>
              {h.comentario && <div>{h.comentario}</div>}
            </li>
          ))}
        </ul>
      </div>
    </PaginaModulo>
  )
}
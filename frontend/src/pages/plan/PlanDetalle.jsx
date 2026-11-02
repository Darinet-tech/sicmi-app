import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CalendarRange, CheckCircle2, Circle } from 'lucide-react'
import api, { textoError } from '../../api'
import ExportarAnexo from '../../ExportarAnexo'
import PaginaModulo from '../../PaginaModulo'
import AccionForm from './AccionForm'
import { CADENA_PLAN, ESTADOS_PLAN, MESES, MESES_ABR, PRIORIDADES, dineroMcup } from './estados'

export default function PlanDetalle() {
  const { id } = useParams()
  const [p, setP] = useState(null)
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [form, setForm] = useState(null) // null cerrado, {} nueva, objeto = editar
  const [devolviendo, setDevolviendo] = useState(false)
  const [motivo, setMotivo] = useState('')

  useEffect(() => {
    api.get(`planes/${id}/`).then((r) => setP(r.data)).catch((e) => setError(textoError(e)))
  }, [id])

  async function llamar(accion, cuerpo = {}) {
    setError('')
    setOcupado(true)
    try {
      const r = await api.post(`planes/${id}/${accion}/`, cuerpo)
      setP(r.data)
      setDevolviendo(false)
      setMotivo('')
    } catch (e) {
      setError(textoError(e))
    } finally {
      setOcupado(false)
    }
  }

  async function eliminar(a) {
    if (!window.confirm(`¿Eliminar la obra «${a.grupo_nombre}» de ${a.inmueble_nombre}?`)) return
    setError('')
    try {
      const r = await api.delete(`acciones-plan/${a.id}/`)
      setP(r.data)
    } catch (e) {
      setError(textoError(e))
    }
  }

  if (!p) return error ? <div className="error">{error}</div> : <p>Cargando...</p>

  const acc = p.acciones_permitidas
  const editable = acc.includes('editar')
  const puedeGenerar = acc.includes('generar')
  const aprobado = p.estado === 'APROBADO'
  const sobrepasa = p.presupuesto_mcup !== null && Number(p.valor_mcup) > Number(p.presupuesto_mcup)

  const porInmueble = {}
  p.acciones.forEach((a) => {
    if (!porInmueble[a.inmueble_nombre]) porInmueble[a.inmueble_nombre] = []
    porInmueble[a.inmueble_nombre].push(a)
  })

  return (
    <PaginaModulo
      icono={CalendarRange}
      titulo={`Plan anual preventivo ${p.anio}`}
      descripcion={`${p.uo_acronimo} · elaborado por ${p.elaborado_por}`}
      acciones={<Link className="btn btn-gris" to="/plan">← Volver</Link>}
    >
      <div className="barra" style={{ marginTop: '-0.5rem' }}>
        <span className={`etiqueta ep-${p.estado}`}>{ESTADOS_PLAN[p.estado]}</span>
      </div>

      <ExportarAnexo titulo="Anexo 9 · Plan anual (REG.4)" ruta={`anexos/plan/${p.id}/`}
        nombre={`Anexo9-Plan-${p.uo_acronimo}-${p.anio}`} />

      {error && <div className="error" style={{ marginTop: '1rem' }}>{error}</div>}
      {p.estado === 'BORRADOR' && p.motivo_devolucion && (
        <div className="aviso" style={{ marginTop: '1rem' }}><strong>Plan devuelto:</strong> {p.motivo_devolucion}</div>
      )}

      <div className="stats" style={{ margin: '1rem 0' }}>
        <div className="stat"><b>{p.num_obras}</b><span>Obras por medios propios</span></div>
        <div className="stat"><b>{p.total_acciones}</b><span>Acciones en el año</span></div>
        <div className={`stat ${sobrepasa ? 'alerta' : ''}`}>
          <b>{dineroMcup(p.valor_mcup)}</b><span>Valor del plan (MCUP)</span>
        </div>
        <div className="stat">
          <b>{p.presupuesto_mcup === null ? '—' : dineroMcup(p.presupuesto_mcup)}</b>
          <span>Presupuesto de {p.anio} (MCUP)</span>
        </div>
      </div>
      {sobrepasa && (
        <div className="aviso">El valor del plan supera el presupuesto cargado para {p.anio}. Revíselo antes de enviarlo a firmas.</div>
      )}

      {form && (
        <AccionForm
          key={form.id || 'nueva'}
          planId={p.id}
          inicial={form}
          onGuardado={(plan) => { setP(plan); setForm(null) }}
          onCancelar={() => setForm(null)}
        />
      )}

      <div className="barra">
        <h3 className="seccion-titulo" style={{ margin: 0 }}>Obras del plan</h3>
        {editable && !form && <button className="btn btn-verde" onClick={() => setForm({})}>+ Nueva obra</button>}
      </div>

      {p.acciones.length === 0 ? (
        <div className="tarjeta">Todavía no hay obras en este plan.</div>
      ) : (
        <div className="tabla-wrap sin-marco">
          <table className="tabla-ficha">
            <thead>
              <tr>
                <th>Obra</th><th>Cant.</th><th>Cronograma</th><th>Valor (MCUP)</th><th>Documentación</th>
                {editable && <th />}
              </tr>
            </thead>
            <tbody>
              {Object.entries(porInmueble).map(([inmueble, lista]) => [
                <tr key={`i-${inmueble}`} className="grupo-fila">
                  <td colSpan={editable ? 6 : 5}>{inmueble}</td>
                </tr>,
                ...lista.map((a) => (
                  <tr key={a.id} style={{ opacity: a.via === 'PROPIOS' ? 1 : 0.7 }}>
                    <td data-label="Obra">
                      <strong>{a.grupo_numero}. {a.grupo_nombre}</strong>
                      {a.descripcion && <div className="sub" style={{ fontWeight: 400 }}>{a.descripcion}</div>}
                      <div>
                        <span className="etiqueta">{a.via_display}</span>{' '}
                        <span className="etiqueta" title={PRIORIDADES[a.prioridad]}>Prioridad {a.prioridad}</span>
                        {a.es_compleja && <span className="etiqueta eo-EN_PROCESO"> Compleja</span>}
                      </div>
                    </td>
                    <td data-label="Cantidad">{a.cantidad}</td>
                    <td data-label="Cronograma">
                      <div className="mini-cal">
                        {MESES_ABR.map((l, i) => {
                          const n = a.programacion[i + 1] || 0
                          return <span key={i} className={n ? 'on' : ''} title={MESES[i]}>{n > 1 ? n : l}</span>
                        })}
                      </div>
                      {aprobado && a.via === 'PROPIOS' && (
                        <div className="chips-mes">
                          {Object.keys(a.programacion).map(Number).sort((x, y) => x - y).map((m) => {
                            const prog = a.programacion[m]
                            const hechas = a.generadas[m] || 0
                            const etq = `${MESES[m - 1].slice(0, 3)} ${hechas}/${prog}`
                            return puedeGenerar && hechas < prog ? (
                              <Link key={m} className="chip-mes abierto" to={`/plan/acciones/${a.id}/generar?mes=${m}`}>
                                {etq} · generar orden
                              </Link>
                            ) : (
                              <span key={m} className="chip-mes">{etq}</span>
                            )
                          })}
                        </div>
                      )}
                      {a.ordenes.length > 0 && (
                        <div style={{ marginTop: 6 }}>
                          {a.ordenes.map((o) => (
                            <Link key={o.id} to={`/ordenes/${o.id}`} style={{ marginRight: 10 }}>
                              {o.codigo} <span className="sub">({o.estado_display})</span>
                            </Link>
                          ))}
                        </div>
                      )}
                    </td>
                    <td data-label="Valor (MCUP)">{dineroMcup(a.valor_estimado)}</td>
                    <td data-label="Documentación">
                      {a.es_compleja && (
                        <span className={`etiqueta ${a.tiene_tt ? 'estado-CERRADA' : 'estado-EN_REVISION'}`}>
                          {a.tiene_tt ? 'Tarea técnica lista' : 'Falta tarea técnica'}
                        </span>
                      )}
                      {a.tiene_croquis && <div className="sub">Con croquis</div>}
                      <div><Link to={`/plan/acciones/${a.id}/documentacion`}>Documentación técnica</Link></div>
                    </td>
                    {editable && (
                      <td data-label="Acciones">
                        <div className="acciones-fila">
                          <button className="btn btn-gris" onClick={() => setForm(a)}>Editar</button>
                          <button className="btn btn-gris" onClick={() => eliminar(a)}>Eliminar</button>
                        </div>
                      </td>
                    )}
                  </tr>
                )),
              ])}
            </tbody>
          </table>
        </div>
      )}

      <div className="tarjeta" style={{ marginTop: '1rem' }}>
        <h3>Firmas</h3>
        <div className="cadena-firmas">
          {CADENA_PLAN.map(([rol, texto]) => {
            const x = p.firmas.find((f) => f.rol === rol)
            return (
              <div key={rol} className={`firma ${x ? 'hecha' : ''}`}>
                {x ? <CheckCircle2 size={22} /> : <Circle size={22} />}
                <div>
                  <b>{texto}</b>
                  <small>{x ? `${x.usuario} · ${new Date(x.fecha).toLocaleString('es')}` : 'Pendiente'}</small>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {(acc.includes('enviar') || acc.includes('firmar')) && (
        <div className="tarjeta">
          <h3>Acciones</h3>
          {devolviendo ? (
            <>
              <label style={{ marginTop: 0 }}>Motivo de la devolución (obligatorio)</label>
              <textarea value={motivo} onChange={(e) => setMotivo(e.target.value)} />
              <div className="fila-botones">
                <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('devolver', { motivo })}>
                  Devolver el plan
                </button>
                <button className="btn btn-gris" onClick={() => setDevolviendo(false)}>Volver</button>
              </div>
            </>
          ) : (
            <div className="fila-botones" style={{ marginTop: 0 }}>
              {acc.includes('enviar') && (
                <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('enviar')}>
                  Enviar a revisión y firmas
                </button>
              )}
              {acc.includes('firmar') && (
                <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('firmar')}>
                  {p.proxima_firma === 'DIRECTOR_UO' ? 'Firmar y aprobar el plan' : 'Firmar el plan'}
                </button>
              )}
              {acc.includes('devolver') && (
                <button className="btn btn-gris" onClick={() => setDevolviendo(true)}>Devolver con observaciones</button>
              )}
            </div>
          )}
        </div>
      )}

      <div className="tarjeta">
        <h3>Historial</h3>
        <ul className="historial">
          {p.historial.map((h, i) => (
            <li key={i}>
              {h.comentario}
              <br />
              <small>{h.usuario} · {new Date(h.fecha).toLocaleString('es')}</small>
            </li>
          ))}
        </ul>
      </div>
    </PaginaModulo>
  )
}
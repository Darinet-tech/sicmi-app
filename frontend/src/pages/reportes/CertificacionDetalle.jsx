import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CheckCircle2, Circle } from 'lucide-react'
import api, { textoError } from '../../api'
import ExportarAnexo from '../../ExportarAnexo'
import { dinero } from '../recursos/estados'
import { CADENA_CERT, ESTADOS_CERT, porc } from './estados'

export default function CertificacionDetalle() {
  const { id } = useParams()
  const [c, setC] = useState(null)
  const [inc, setInc] = useState({})
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [devolviendo, setDevolviendo] = useState(false)
  const [motivo, setMotivo] = useState('')

  function cargar(datos) {
    setC(datos)
    setInc(Object.fromEntries(datos.filas.map((f) => [f.clave, f.incidencia])))
  }

  useEffect(() => {
    api.get(`certificaciones/${id}/`).then((r) => cargar(r.data)).catch((e) => setError(textoError(e)))
  }, [id])

  async function llamar(accion, cuerpo = {}) {
    setError('')
    setOk('')
    setOcupado(true)
    try {
      const r = await api.post(`certificaciones/${id}/${accion}/`, cuerpo)
      cargar(r.data)
      setDevolviendo(false)
      setMotivo('')
      return true
    } catch (e) {
      setError(textoError(e))
      return false
    } finally {
      setOcupado(false)
    }
  }

  async function guardarInc() {
    if (await llamar('incidencias', { incidencias: inc })) setOk('Incidencias guardadas.')
  }

  async function enviar() {
    // Guarda primero lo escrito, para no perderlo
    if (await llamar('incidencias', { incidencias: inc })) await llamar('enviar')
  }

  if (!c) return error ? <div className="error">{error}</div> : <p>Cargando...</p>

  const acc = c.acciones_permitidas
  const editable = acc.includes('incidencias')
  const ind = c.indicadores

  return (
    <>
      <div className="barra">
        <h2>
          Certificación de {c.mes_nombre} {c.anio} · {c.uo_acronimo}{' '}
          <span className={`etiqueta ec-${c.estado}`}>{ESTADOS_CERT[c.estado]}</span>
        </h2>
        <Link className="btn btn-gris" to="/reportes/certificaciones">← Volver</Link>
      </div>

      <ExportarAnexo titulo="Anexo 10 · Certificación mensual (REG.5)" ruta={`anexos/certificacion/${c.id}/`}
        nombre={`Anexo10-Certificacion-${c.uo_acronimo}-${c.anio}-${String(c.mes).padStart(2, '0')}`} />

      {error && <div className="error" style={{ marginTop: '1rem' }}>{error}</div>}
      {ok && <div className="exito" style={{ marginTop: '1rem' }}>{ok}</div>}
      {c.vencida && (
        <div className="error" style={{ marginTop: '1rem' }}>
          El plazo de envío a Inmobiliaria (día 5 del mes siguiente) ya venció y la certificación no está aprobada.
        </div>
      )}
      {c.mes_en_curso && c.estado === 'BORRADOR' && (
        <div className="aviso" style={{ marginTop: '1rem' }}>
          El mes todavía no ha terminado. Use «Actualizar datos» al cierre del último día antes de enviarla a firmas.
        </div>
      )}
      {c.estado === 'BORRADOR' && c.motivo_devolucion && (
        <div className="aviso" style={{ marginTop: '1rem' }}><strong>Devuelta:</strong> {c.motivo_devolucion}</div>
      )}

      {ind && (
        <div className="stats" style={{ margin: '1rem 0' }}>
          <div className="stat"><b>{porc(ind.plan_fisico.mes.pct)}</b><span>Cumplimiento del plan físico (mes)</span></div>
          <div className="stat"><b>{porc(ind.satisfaccion.mes.pct)}</b><span>Satisfacción del correctivo (mes)</span></div>
          <div className="stat"><b>{porc(ind.gastos.pct)}</b><span>Del presupuesto gastado ({dinero(ind.gastos.gastado)} CUP)</span></div>
        </div>
      )}

      <div className="tarjeta">
        <h3>Acciones constructivas del mes</h3>
        {c.filas.length === 0 ? (
          <p style={{ color: 'var(--gris)' }}>
            No hay acciones planificadas ni ejecutadas este mes. La certificación puede enviarse así, en cero.
          </p>
        ) : (
          <div className="tabla-wrap">
            <table>
              <thead>
                <tr>
                  <th>Inmueble</th><th>Resumen de acciones</th><th>Prev. plan</th><th>Prev. real</th>
                  <th>%</th><th>Correctivas</th><th>Total</th><th>Incidencias</th>
                </tr>
              </thead>
              <tbody>
                {c.filas.map((f) => (
                  <tr key={f.clave}>
                    <td>{f.inmueble}</td>
                    <td>{f.grupo_num === 99 ? f.grupo : `Mantenimiento y reparación menor de ${f.grupo}`}</td>
                    <td>{f.plan}</td>
                    <td>{f.real}</td>
                    <td>{porc(f.pct)}</td>
                    <td>{f.correctivas}</td>
                    <td><strong>{f.total}</strong></td>
                    <td style={{ minWidth: 220 }}>
                      {editable ? (
                        <input type="text" maxLength={300} value={inc[f.clave] || ''}
                          placeholder="Tarea Vida, plan de prevención, etc."
                          onChange={(e) => setInc({ ...inc, [f.clave]: e.target.value })} />
                      ) : (
                        f.incidencia
                      )}
                      {f.auto && <div className="sub" style={{ fontWeight: 400 }}>{f.auto}</div>}
                    </td>
                  </tr>
                ))}
                <tr className="total-fila">
                  <td colSpan={2}>Resumen total de acciones</td>
                  <td>{c.resumen.plan}</td>
                  <td>{c.resumen.real}</td>
                  <td>{porc(c.resumen.pct)}</td>
                  <td>{c.resumen.correctivas}</td>
                  <td>{c.resumen.total}</td>
                  <td />
                </tr>
              </tbody>
            </table>
          </div>
        )}
        <p style={{ marginBottom: 0 }}>
          <span className="sub">Inmuebles donde se ejecutaron acciones constructivas:</span> <strong>{c.resumen.inmuebles}</strong>
        </p>
        {c.generada && (
          <small className="pista" style={{ color: 'var(--gris)' }}>
            Datos calculados el {new Date(c.generada).toLocaleString('es')}.
          </small>
        )}
      </div>

      <div className="tarjeta">
        <h3>Firmas</h3>
        <div className="cadena-firmas">
          {CADENA_CERT.map(([rol, texto]) => {
            const x = c.firmas.find((f) => f.rol === rol)
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

      {acc.length > 0 && (
        <div className="tarjeta">
          <h3>Acciones</h3>
          {devolviendo ? (
            <>
              <label style={{ marginTop: 0 }}>Motivo de la devolución (obligatorio)</label>
              <textarea value={motivo} onChange={(e) => setMotivo(e.target.value)} />
              <div className="fila-botones">
                <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('devolver', { motivo })}>
                  Devolver la certificación
                </button>
                <button className="btn btn-gris" onClick={() => setDevolviendo(false)}>Volver</button>
              </div>
            </>
          ) : (
            <div className="fila-botones" style={{ marginTop: 0 }}>
              {acc.includes('actualizar') && (
                <button className="btn btn-gris" disabled={ocupado} onClick={() => llamar('actualizar')}>Actualizar datos</button>
              )}
              {acc.includes('incidencias') && (
                <button className="btn btn-gris" disabled={ocupado} onClick={guardarInc}>Guardar incidencias</button>
              )}
              {acc.includes('enviar') && (
                <button className="btn btn-verde" disabled={ocupado} onClick={enviar}>Enviar a revisión y firmas</button>
              )}
              {acc.includes('firmar') && (
                <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('firmar')}>
                  {c.proxima_firma === 'JEFE_LOGISTICA' ? 'Firmar y aprobar' : 'Firmar'}
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
          {c.historial.map((h, i) => (
            <li key={i}>
              {h.comentario}
              <br />
              <small>{h.usuario} · {new Date(h.fecha).toLocaleString('es')}</small>
            </li>
          ))}
        </ul>
      </div>
    </>
  )
}
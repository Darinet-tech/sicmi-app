import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CheckCircle2, Circle } from 'lucide-react'
import api, { textoError } from '../../api'
import { dinero } from './estados'
import { EtiquetaRecurso } from './ListaRecursos'

const fecha = (f) => (f ? new Date(f).toLocaleString('es') : '')
const num = (v) => Number(v || 0)
const SOBRANTE_VACIO = { linea: null, cantidad: '', destino: 'DEVOLUCION', vale_devolucion: '' }

export default function DetalleRecurso() {
  const { id } = useParams()
  const [s, setS] = useState(null)
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [modo, setModo] = useState(null) // 'rechazar' | 'cancelar' | 'despachar'
  const [motivo, setMotivo] = useState('')
  const [vale, setVale] = useState('')
  const [desp, setDesp] = useState({})
  const [sob, setSob] = useState(null) // formulario de sobrante abierto

  function cargar(datos) {
    setS(datos)
    const mapa = {}
    datos.lineas.forEach((l) => { mapa[l.id] = l.cantidad })
    setDesp(mapa)
  }

  useEffect(() => {
    api.get(`solicitudes-recursos/${id}/`).then((r) => cargar(r.data)).catch((e) => setError(textoError(e)))
  }, [id])

  async function llamar(accion, cuerpo = {}) {
    setError('')
    setOcupado(true)
    try {
      const r = await api.post(`solicitudes-recursos/${id}/${accion}/`, cuerpo)
      cargar(r.data)
      setModo(null)
      setMotivo('')
      setSob(null)
    } catch (e) {
      setError(textoError(e))
    } finally {
      setOcupado(false)
    }
  }

  if (!s) return error ? <div className="error">{error}</div> : <p>Cargando...</p>

  const acc = s.acciones
  const p = s.presupuesto
  const abierta = ['SOLICITADA', 'PENDIENTE_SOBREGIRO', 'VERIFICADA', 'AUTORIZADA'].includes(s.estado)
  const despachada = s.estado === 'DESPACHADA'
  const despachando = modo === 'despachar'
  const puedeSobrante = acc.includes('sobrante')
  const accionesGestion = acc.filter((a) => a !== 'sobrante')

  const antesImporte = 4 + (abierta ? 1 : 0) + (despachada ? 4 : 0) + (despachando ? 1 : 0) + 1
  const restante = (l) => num(l.cantidad_despachada) - num(l.devuelta) - num(l.custodia)

  const pasos = [
    ['Solicitado por', s.solicitada_por, s.creada],
    ['Financiamiento verificado por', s.verificada_por, s.fecha_verificacion],
    ['Autorizado por', s.autorizada_por, s.fecha_autorizacion],
    ['Despachado y recibido por', s.despachada_por, s.fecha_despacho],
  ]

  return (
    <>
      <div className="barra">
        <h2>
          Solicitud de recursos {s.codigo} <EtiquetaRecurso estado={s.estado} />
        </h2>
        <Link className="btn btn-gris" to="/recursos/solicitudes">← Volver</Link>
      </div>

      {error && <div className="error">{error}</div>}
      {s.estado === 'PENDIENTE_SOBREGIRO' && (
        <div className="aviso">
          El presupuesto disponible ({dinero(p.disponible)} CUP) no alcanza para esta solicitud ({dinero(s.total)} CUP).
          El Director de la UO debe solicitar un sobregiro en <Link to="/recursos/presupuesto">Presupuesto y sobregiros</Link>.
          Cuando el nivel central lo apruebe, el Especialista vuelve a pulsar «Verificar financiamiento».
        </div>
      )}
      {(s.estado === 'RECHAZADA' || s.estado === 'CANCELADA') && s.motivo && (
        <div className="aviso"><strong>Motivo:</strong> {s.motivo}</div>
      )}
      {despachada && !s.sobrantes_revisados && puedeSobrante && (
        <div className="aviso">
          Registre los sobrantes de materiales (si los hay) y confirme que no hay más. La orden no se podrá
          entregar al cliente hasta entonces.
        </div>
      )}

      <div className="tarjeta">
        <h3>Datos</h3>
        <dl className="datos">
          <dt>Orden de trabajo</dt><dd><Link to={`/ordenes/${s.orden}`}>{s.orden_codigo}</Link></dd>
          <dt>Destino (inmueble)</dt><dd>{s.inmueble}</dd>
          <dt>Centro de costo</dt><dd>{s.centro_costo}</dd>
          <dt>Almacén</dt><dd>{s.almacen_nombre}</dd>
          {s.vale_numero && (<><dt>No. de vale de salida</dt><dd>{s.vale_numero}</dd></>)}
          {despachada && (
            <>
              <dt>Sobrantes</dt>
              <dd>{s.sobrantes_revisados ? 'Verificados' : 'Pendientes de verificar'}</dd>
            </>
          )}
        </dl>
      </div>

      <div className="tarjeta">
        <h3>Materiales</h3>
        <div className="tabla-wrap">
          <table>
            <thead>
              <tr>
                <th>Código SAP</th><th>Descripción</th><th>UM</th><th>Solicitada</th>
                {abierta && <th>En almacén</th>}
                {despachada && (<><th>Despachada</th><th>Devuelta</th><th>En custodia</th><th>Utilizada</th></>)}
                {despachando && <th>Despachada</th>}
                <th>Precio</th><th>Importe</th>
                {puedeSobrante && <th />}
              </tr>
            </thead>
            <tbody>
              {s.lineas.map((l) => (
                <tr key={l.id} className={abierta && num(l.stock) < num(l.cantidad) ? 'fila-alerta' : ''}>
                  <td>{l.codigo_sap}</td>
                  <td>{l.descripcion}</td>
                  <td>{l.um}</td>
                  <td>{l.cantidad}</td>
                  {abierta && <td>{l.stock}</td>}
                  {despachada && (
                    <>
                      <td>{l.cantidad_despachada}</td>
                      <td>{l.devuelta}</td>
                      <td>{l.custodia}</td>
                      <td><strong>{l.utilizada}</strong></td>
                    </>
                  )}
                  {despachando && (
                    <td style={{ minWidth: 110 }}>
                      <input type="number" min="0" max={l.cantidad} step="0.001" value={desp[l.id] ?? ''}
                        onChange={(e) => setDesp({ ...desp, [l.id]: e.target.value })} />
                    </td>
                  )}
                  <td>{dinero(l.precio_unitario)}</td>
                  <td>{dinero(l.importe)}</td>
                  {puedeSobrante && (
                    <td>
                      {restante(l) > 0.0005 && (
                        <button className="btn btn-gris" onClick={() => setSob({ ...SOBRANTE_VACIO, linea: l.id })}>
                          Registrar sobrante
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
              <tr className="total-fila">
                <td colSpan={antesImporte}>{despachada ? 'Valor utilizado (CUP)' : 'Total (CUP)'}</td>
                <td colSpan={puedeSobrante ? 2 : 1}>{dinero(s.total)}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {sob && (
          <div className="tarjeta" style={{ marginTop: '1rem', background: '#f7f8fa' }}>
            <h3>Registrar sobrante · {s.lineas.find((l) => l.id === sob.linea)?.codigo_sap}</h3>
            <div className="form-grid">
              <div>
                <label style={{ marginTop: 0 }}>
                  Cantidad sobrante (máx. {restante(s.lineas.find((l) => l.id === sob.linea)).toFixed(3)})
                </label>
                <input type="number" min="0" step="0.001" value={sob.cantidad}
                  onChange={(e) => setSob({ ...sob, cantidad: e.target.value })} />
              </div>
              <div>
                <label style={{ marginTop: 0 }}>Destino del sobrante</label>
                <select value={sob.destino} onChange={(e) => setSob({ ...sob, destino: e.target.value })}>
                  <option value="DEVOLUCION">Devolver al almacén</option>
                  <option value="CUSTODIA">Queda en custodia del Jefe de Brigada</option>
                </select>
              </div>
              {sob.destino === 'DEVOLUCION' && (
                <div className="campo-completo">
                  <label style={{ marginTop: 0 }}>No. del vale de devolución</label>
                  <input type="text" maxLength={30} value={sob.vale_devolucion}
                    onChange={(e) => setSob({ ...sob, vale_devolucion: e.target.value })} />
                </div>
              )}
            </div>
            <div className="fila-botones">
              <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('registrar_sobrante', sob)}>
                Guardar sobrante
              </button>
              <button className="btn btn-gris" onClick={() => setSob(null)}>Cancelar</button>
            </div>
          </div>
        )}
      </div>

      {s.sobrantes.length > 0 && (
        <div className="tarjeta">
          <h3>Sobrantes registrados</h3>
          <div className="tabla-wrap">
            <table>
              <thead>
                <tr><th>Material</th><th>Cantidad</th><th>Destino</th><th>Detalle</th><th>Registrado por</th></tr>
              </thead>
              <tbody>
                {s.sobrantes.map((x) => (
                  <tr key={x.id}>
                    <td>{x.codigo_sap} · {x.descripcion}</td>
                    <td>{x.cantidad}</td>
                    <td>{x.destino_display}</td>
                    <td>
                      {x.destino === 'DEVOLUCION'
                        ? `Vale ${x.vale_devolucion}`
                        : x.orden_destino ? `Usado en la orden ${x.orden_destino}` : 'Pendiente de asignar a una orden'}
                    </td>
                    <td>{x.registrado_por}<div className="sub">{fecha(x.fecha)}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {abierta && (
        <div className="stats" style={{ marginBottom: '1rem' }}>
          <div className="stat"><b>{dinero(p.disponible)}</b><span>Presupuesto disponible {p.anio}</span></div>
          <div className="stat"><b>{dinero(p.comprometido)}</b><span>Comprometido (autorizado)</span></div>
          <div className="stat"><b>{dinero(p.gastado)}</b><span>Gastado</span></div>
        </div>
      )}

      <div className="tarjeta">
        <h3>Firmas del Anexo 3</h3>
        <div className="cadena-firmas">
          {pasos.map(([texto, quien, cuando]) => (
            <div key={texto} className={`firma ${quien ? 'hecha' : ''}`}>
              {quien ? <CheckCircle2 size={22} /> : <Circle size={22} />}
              <div>
                <b>{texto}</b>
                <small>{quien ? `${quien} · ${fecha(cuando)}` : 'Pendiente'}</small>
              </div>
            </div>
          ))}
        </div>
      </div>

      {accionesGestion.length > 0 && (
        <div className="tarjeta">
          <h3>Acciones</h3>

          {despachando && (
            <>
              <label style={{ marginTop: 0 }}>Número del vale de salida del almacén</label>
              <input type="text" value={vale} onChange={(e) => setVale(e.target.value)} maxLength={30} />
              <small className="pista">Ajuste las cantidades de la tabla si no salió todo lo autorizado.</small>
            </>
          )}
          {(modo === 'rechazar' || modo === 'cancelar') && (
            <>
              <label style={{ marginTop: 0 }}>
                {modo === 'rechazar' ? 'Motivo del rechazo (obligatorio)' : 'Motivo de la cancelación (opcional)'}
              </label>
              <textarea value={motivo} onChange={(e) => setMotivo(e.target.value)} />
            </>
          )}

          <div className="fila-botones" style={{ marginTop: modo ? '1rem' : 0 }}>
            {!modo && acc.includes('verificar') && (
              <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('verificar')}>
                Verificar financiamiento
              </button>
            )}
            {!modo && acc.includes('autorizar') && (
              <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('autorizar')}>Autorizar</button>
            )}
            {!modo && acc.includes('despachar') && (
              <button className="btn btn-verde" onClick={() => setModo('despachar')}>Registrar despacho</button>
            )}
            {!modo && acc.includes('revisar_sobrantes') && (
              <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('revisar_sobrantes')}>
                Confirmar que no hay más sobrantes
              </button>
            )}
            {!modo && acc.includes('rechazar') && (
              <button className="btn btn-gris" onClick={() => setModo('rechazar')}>Rechazar</button>
            )}
            {!modo && acc.includes('cancelar') && (
              <button className="btn btn-peligro" onClick={() => setModo('cancelar')}>Cancelar solicitud</button>
            )}

            {despachando && (
              <button className="btn btn-verde" disabled={ocupado}
                onClick={() => llamar('despachar', {
                  vale_numero: vale,
                  lineas: s.lineas.map((l) => ({ id: l.id, cantidad_despachada: desp[l.id] })),
                })}>
                Confirmar despacho
              </button>
            )}
            {modo === 'rechazar' && (
              <button className="btn btn-verde" disabled={ocupado} onClick={() => llamar('rechazar', { motivo })}>
                Confirmar rechazo
              </button>
            )}
            {modo === 'cancelar' && (
              <button className="btn btn-peligro" disabled={ocupado} onClick={() => llamar('cancelar', { motivo })}>
                Confirmar cancelación
              </button>
            )}
            {modo && <button className="btn btn-gris" onClick={() => setModo(null)}>Volver</button>}
          </div>
        </div>
      )}
    </>
  )
}
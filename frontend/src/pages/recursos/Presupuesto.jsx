import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { dinero } from './estados'

function FilaSobregiro({ s, esCentral, onResuelto, onError }) {
  const [monto, setMonto] = useState(s.monto_solicitado)
  const [respuesta, setRespuesta] = useState('')
  const [ocupado, setOcupado] = useState(false)

  async function resolver(aprobar) {
    onError('')
    setOcupado(true)
    try {
      const r = await api.post(`sobregiros/${s.id}/resolver/`, { aprobar, monto_aprobado: monto, respuesta })
      onResuelto(r.data)
    } catch (e) {
      onError(textoError(e))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <tr>
      <td>{s.uo_acronimo} · {s.anio}</td>
      <td>{dinero(s.monto_solicitado)}</td>
      <td style={{ maxWidth: 260 }}>{s.fundamentacion}<div className="sub">{s.solicitado_por}</div></td>
      <td>
        <span className={`etiqueta er-${s.estado === 'APROBADO' ? 'DESPACHADA' : s.estado === 'RECHAZADO' ? 'RECHAZADA' : 'SOLICITADA'}`}>
          {s.estado_display}
        </span>
        {s.estado === 'APROBADO' && <div>{dinero(s.monto_aprobado)} CUP</div>}
        {s.respuesta && <div className="sub">{s.respuesta}</div>}
      </td>
      <td style={{ minWidth: 220 }}>
        {esCentral && s.estado === 'SOLICITADO' && (
          <div className="estado-edit">
            <input type="number" min="0" step="0.01" value={monto} onChange={(e) => setMonto(e.target.value)} />
            <input type="text" placeholder="Respuesta (obligatoria si rechaza)" value={respuesta}
              onChange={(e) => setRespuesta(e.target.value)} />
            <div className="acciones-fila">
              <button className="btn btn-verde" disabled={ocupado} onClick={() => resolver(true)}>Aprobar</button>
              <button className="btn btn-gris" disabled={ocupado} onClick={() => resolver(false)}>Rechazar</button>
            </div>
          </div>
        )}
      </td>
    </tr>
  )
}

export default function Presupuesto() {
  const { usuario } = useAuth()
  const esDirector = usuario.rol === 'DIRECTOR_UO'
  const esCentral = usuario.rol === 'CENTRAL'
  const anio = new Date().getFullYear()

  const [resumenes, setResumenes] = useState([])
  const [sobregiros, setSobregiros] = useState([])
  const [form, setForm] = useState({ monto_solicitado: '', fundamentacion: '' })
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  function cargar() {
    Promise.all([api.get('presupuesto/', { params: { anio } }), api.get('sobregiros/')])
      .then(([p, s]) => {
        setResumenes(p.data)
        setSobregiros(s.data)
      })
      .catch((e) => setError(textoError(e)))
  }
  useEffect(cargar, [anio])

  async function solicitar(e) {
    e.preventDefault()
    setError('')
    setOk('')
    try {
      await api.post('sobregiros/', form)
      setForm({ monto_solicitado: '', fundamentacion: '' })
      setOk('Solicitud de sobregiro enviada al nivel central.')
      cargar()
    } catch (err) {
      setError(textoError(err))
    }
  }

  const mio = resumenes[0]

  return (
    <>
      {error && <div className="error">{error}</div>}
      {ok && <div className="exito">{ok}</div>}

      {resumenes.map((r) => (
        <div key={r.uo}>
          <h3 className="seccion-titulo" style={{ marginTop: 0 }}>{r.uo} · {r.anio}</h3>
          {!r.configurado && (
            <div className="aviso">Esta UO no tiene presupuesto cargado para {r.anio} (Admin → Presupuestos anuales).</div>
          )}
          <div className="stats" style={{ marginBottom: '1rem' }}>
            <div className="stat"><b>{dinero(r.asignado)}</b><span>Asignado</span></div>
            <div className="stat"><b>{dinero(r.sobregiros_aprobados)}</b><span>Sobregiros aprobados</span></div>
            <div className="stat"><b>{dinero(r.gastado)}</b><span>Gastado</span></div>
            <div className="stat"><b>{dinero(r.comprometido)}</b><span>Comprometido</span></div>
            <div className={`stat ${r.disponible < 0 ? 'alerta' : ''}`}>
              <b>{dinero(r.disponible)}</b><span>Disponible</span>
            </div>
          </div>
        </div>
      ))}

      {esDirector && mio && (
        <form className="tarjeta" onSubmit={solicitar}>
          <h3>Solicitar sobregiro</h3>
          <p style={{ marginTop: 0, color: 'var(--gris)' }}>
            Financiamiento asignado: {dinero(mio.asignado)} CUP · Real gastado hasta la fecha: {dinero(mio.gastado)} CUP
          </p>
          <label style={{ marginTop: 0 }}>Sobregiro solicitado en el año (CUP)</label>
          <input type="number" min="0" step="0.01" value={form.monto_solicitado} required
            onChange={(e) => setForm({ ...form, monto_solicitado: e.target.value })} />
          <label>Fundamentación</label>
          <textarea value={form.fundamentacion} required
            onChange={(e) => setForm({ ...form, fundamentacion: e.target.value })} />
          <div className="fila-botones">
            <button className="btn btn-verde">Enviar solicitud</button>
          </div>
        </form>
      )}

      <h3 className="seccion-titulo">Sobregiros</h3>
      {sobregiros.length === 0 ? (
        <div className="tarjeta">No hay sobregiros solicitados.</div>
      ) : (
        <div className="tabla-wrap">
          <table>
            <thead>
              <tr><th>UO · año</th><th>Solicitado (CUP)</th><th>Fundamentación</th><th>Estado</th><th /></tr>
            </thead>
            <tbody>
              {sobregiros.map((s) => (
                <FilaSobregiro
                  key={s.id} s={s} esCentral={esCentral} onError={setError}
                  onResuelto={(nuevo) => { setSobregiros(sobregiros.map((x) => (x.id === nuevo.id ? nuevo : x))); cargar() }}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
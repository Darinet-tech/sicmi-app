import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { ESTADOS_CERT, MESES, porc } from './estados'

export default function Certificaciones() {
  const { usuario } = useAuth()
  const navigate = useNavigate()
  const puedeCrear = usuario.rol === 'ESPECIALISTA'

  // Por defecto, el mes anterior: es el que se certifica
  const hoy = new Date()
  const prev = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1)
  const [form, setForm] = useState({ anio: prev.getFullYear(), mes: prev.getMonth() + 1 })
  const [lista, setLista] = useState([])
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    api
      .get('certificaciones/')
      .then((r) => setLista(r.data))
      .catch((e) => setError(textoError(e)))
      .finally(() => setCargando(false))
  }, [])

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      const r = await api.post('certificaciones/', { anio: Number(form.anio), mes: Number(form.mes) })
      navigate(`/reportes/certificaciones/${r.data.id}`)
    } catch (err) {
      setError(textoError(err))
    }
  }

  return (
    <>
      {puedeCrear && (
        <form className="tarjeta" onSubmit={crear}>
          <h3>Nueva certificación mensual</h3>
          <p style={{ marginTop: 0, color: 'var(--gris)' }}>
            Se arma con los datos del sistema: plan frente a real en las preventivas y las correctivas ejecutadas.
            Debe enviarse a Inmobiliaria antes del día 5 del mes siguiente.
          </p>
          <div className="controles">
            <div>
              <label style={{ marginTop: 0 }}>Mes</label>
              <select value={form.mes} onChange={(e) => setForm({ ...form, mes: e.target.value })}>
                {MESES.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div>
              <label style={{ marginTop: 0 }}>Año</label>
              <input type="number" min="2000" max="2100" value={form.anio} style={{ width: 100 }}
                onChange={(e) => setForm({ ...form, anio: e.target.value })} />
            </div>
            <button className="btn btn-verde">Generar certificación</button>
          </div>
        </form>
      )}

      {error && <div className="error">{error}</div>}
      {cargando ? (
        <p>Cargando...</p>
      ) : lista.length === 0 ? (
        <div className="tarjeta">Todavía no hay certificaciones.</div>
      ) : (
        <div className="tabla-wrap sin-marco">
          <table className="tabla-ficha">
            <thead>
              <tr><th>Mes</th><th>Preventivas (real/plan)</th><th>Correctivas</th><th>Total</th><th>Plazo</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {lista.map((c) => (
                <tr key={c.id}>
                  <td data-label="Mes">
                    <Link to={`/reportes/certificaciones/${c.id}`}><strong>{c.mes_nombre} {c.anio}</strong></Link>
                    <div className="sub">{c.uo_acronimo}</div>
                  </td>
                  <td data-label="Preventivas">{c.resumen.real} / {c.resumen.plan} ({porc(c.resumen.pct)})</td>
                  <td data-label="Correctivas">{c.resumen.correctivas}</td>
                  <td data-label="Total">{c.resumen.total}</td>
                  <td data-label="Plazo">
                    {new Date(c.limite + 'T00:00:00').toLocaleDateString('es')}
                    {c.vencida && <span className="etiqueta urgente">VENCIDA</span>}
                  </td>
                  <td data-label="Estado"><span className={`etiqueta ec-${c.estado}`}>{ESTADOS_CERT[c.estado]}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
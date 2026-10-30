import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { textoError } from '../api'
import { useAuth } from '../AuthContext'

export default function GenerarOrden({ solicitud }) {
  const { usuario } = useAuth()
  const navigate = useNavigate()
  const [brigadas, setBrigadas] = useState([])
  const [vehiculos, setVehiculos] = useState([])
  const [brigada, setBrigada] = useState('')
  const [vehiculo, setVehiculo] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  const puede =
    usuario.rol === 'ESPECIALISTA' && solicitud.estado === 'EN_PROGRAMACION' && !solicitud.orden_id

  useEffect(() => {
    if (!puede) return
    Promise.all([api.get('brigadas/'), api.get('vehiculos/')])
      .then(([b, v]) => {
        setBrigadas(b.data.filter((x) => x.activa))
        setVehiculos(v.data.filter((x) => x.activo))
      })
      .catch((e) => setError(textoError(e)))
  }, [puede])

  if (solicitud.orden_id) {
    return (
      <div className="tarjeta">
        <h3>Orden de trabajo</h3>
        <p>
          Esta solicitud tiene la orden <strong>{solicitud.orden_codigo}</strong>.
        </p>
        <Link className="btn btn-verde" to={`/ordenes/${solicitud.orden_id}`}>Abrir orden</Link>
      </div>
    )
  }
  if (!puede) return null

  async function generar() {
    setError('')
    setEnviando(true)
    try {
      const r = await api.post(`solicitudes/${solicitud.id}/generar-orden/`, {
        brigada: brigada ? Number(brigada) : null,
        vehiculo: vehiculo ? Number(vehiculo) : null,
      })
      navigate(`/ordenes/${r.data.id}`)
    } catch (e) {
      setError(textoError(e))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="tarjeta">
      <h3>Generar orden de trabajo</h3>
      <p style={{ color: 'var(--gris)', marginTop: 0 }}>
        Se le asignará el consecutivo de su UO. Al elegir la brigada se agregan sus miembros que hoy figuren como Trabajando.
      </p>
      <label style={{ marginTop: 0 }}>Brigada</label>
      <select value={brigada} onChange={(e) => setBrigada(e.target.value)}>
        <option value="">-- La asignaré después --</option>
        {brigadas.map((b) => <option key={b.id} value={b.id}>{b.nombre}</option>)}
      </select>
      <label>Vehículo (opcional)</label>
      <select value={vehiculo} onChange={(e) => setVehiculo(e.target.value)}>
        <option value="">-- Sin vehículo --</option>
        {vehiculos.map((v) => <option key={v.id} value={v.id}>{v.chapa} {v.tipo}</option>)}
      </select>
      {error && <div className="error">{error}</div>}
      <div className="fila-botones">
        <button className="btn btn-verde" onClick={generar} disabled={enviando}>
          {enviando ? 'Generando...' : 'Generar orden de trabajo'}
        </button>
      </div>
    </div>
  )
}
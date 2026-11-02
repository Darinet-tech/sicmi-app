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
    const enProceso = solicitud.estado === 'EN_PROGRAMACION'
    return (
      <div className="tarjeta">
        <h3>Orden de trabajo</h3>
        <p>
          {enProceso
            ? 'Esta solicitud tiene una orden en proceso, todavía sin generar.'
            : <>Esta solicitud tiene la orden <strong>{solicitud.orden_codigo}</strong>.</>}
        </p>
        {usuario.rol !== 'CLIENTE' || !enProceso ? (
          <Link className="btn btn-verde" to={`/ordenes/${solicitud.orden_id}`}>Abrir orden</Link>
        ) : null}
      </div>
    )
  }
  if (!puede) return null

  async function crear() {
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
      <h3>Preparar orden de trabajo</h3>
      <p style={{ color: 'var(--gris)', marginTop: 0 }}>
        Se crea En proceso, sin número oficial. Podrá solicitar los recursos y completar los datos, y la orden
        se generará cuando se cumplan todos los requisitos, entre ellos el número del vale de salida de los materiales.
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
        <button className="btn btn-verde" onClick={crear} disabled={enviando}>
          {enviando ? 'Creando...' : 'Crear orden en proceso'}
        </button>
      </div>
    </div>
  )
}
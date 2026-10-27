import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { textoError } from '../api'
import { useAuth } from '../AuthContext'

export const ESTADOS = {
  ENVIADA: 'Enviada',
  EN_REVISION: 'En revisión',
  DEVUELTA: 'Devuelta al cliente',
  EN_INSPECCION: 'En inspección',
  EN_PROGRAMACION: 'En programación',
  ORDEN_GENERADA: 'Orden generada',
  CERRADA: 'Cerrada',
  CANCELADA: 'Cancelada',
}

export function Etiqueta({ estado }) {
  return <span className={`etiqueta estado-${estado}`}>{ESTADOS[estado]}</span>
}

export default function Solicitudes() {
  const { usuario } = useAuth()
  const [lista, setLista] = useState([])
  const [filtro, setFiltro] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    api
      .get('solicitudes/')
      .then((r) => setLista(r.data))
      .catch((e) => setError(textoError(e)))
      .finally(() => setCargando(false))
  }, [])

  const visibles = filtro ? lista.filter((s) => s.estado === filtro) : lista

  return (
    <>
      <div className="barra">
        <h2>Solicitudes de mantenimiento</h2>
        {usuario.rol === 'CLIENTE' && (
          <Link className="btn btn-verde" to="/solicitudes/nueva">
            + Nueva solicitud
          </Link>
        )}
      </div>

      <div className="tarjeta">
        <label style={{ marginTop: 0 }}>Filtrar por estado</label>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ maxWidth: 260 }}>
          <option value="">Todos</option>
          {Object.entries(ESTADOS).map(([valor, texto]) => (
            <option key={valor} value={valor}>{texto}</option>
          ))}
        </select>
      </div>

      {error && <div className="error">{error}</div>}
      {cargando ? (
        <p>Cargando...</p>
      ) : visibles.length === 0 ? (
        <div className="tarjeta">No hay solicitudes para mostrar.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>No.</th>
              <th>Inmueble</th>
              <th>Local</th>
              <th>Solicitante</th>
              <th>Fecha</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {visibles.map((s) => (
              <tr key={s.id}>
                <td><Link to={`/solicitudes/${s.id}`}>#{s.id}</Link></td>
                <td>{s.inmueble_nombre}</td>
                <td>{s.local}</td>
                <td>{s.solicitante_nombre}</td>
                <td>{new Date(s.creada).toLocaleDateString('es')}</td>
                <td>
                  <Etiqueta estado={s.estado} />
                  {s.es_urgente && <span className="etiqueta urgente">URGENTE</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
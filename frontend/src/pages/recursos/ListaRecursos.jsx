import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { ESTADOS_RECURSO, dinero } from './estados'

export function EtiquetaRecurso({ estado }) {
  return <span className={`etiqueta er-${estado}`}>{ESTADOS_RECURSO[estado]}</span>
}

export default function ListaRecursos() {
  const { usuario } = useAuth()
  const puedeCrear = usuario.rol === 'ESPECIALISTA' || usuario.rol === 'JEFE_BRIGADA'
  const [lista, setLista] = useState([])
  const [filtro, setFiltro] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    api
      .get('solicitudes-recursos/')
      .then((r) => setLista(r.data))
      .catch((e) => setError(textoError(e)))
      .finally(() => setCargando(false))
  }, [])

  const visibles = filtro ? lista.filter((s) => s.estado === filtro) : lista

  return (
    <>
      <div className="tarjeta">
        <div className="barra" style={{ marginBottom: 0 }}>
          <div>
            <label style={{ marginTop: 0 }}>Filtrar por estado</label>
            <select value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ maxWidth: 260 }}>
              <option value="">Todos</option>
              {Object.entries(ESTADOS_RECURSO).map(([v, t]) => (
                <option key={v} value={v}>{t}</option>
              ))}
            </select>
          </div>
          {puedeCrear && (
            <Link className="btn btn-verde" to="/recursos/solicitudes/nueva">+ Nueva solicitud de recursos</Link>
          )}
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {cargando ? (
        <p>Cargando...</p>
      ) : visibles.length === 0 ? (
        <div className="tarjeta">No hay solicitudes de recursos para mostrar.</div>
      ) : (
        <div className="tabla-wrap sin-marco">
          <table className="tabla-ficha">
            <thead>
              <tr>
                <th>Solicitud</th>
                <th>Orden / inmueble</th>
                <th>Almacén</th>
                <th>Solicitada por</th>
                <th>Total (CUP)</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((s) => (
                <tr key={s.id}>
                  <td data-label="Solicitud">
                    <Link to={`/recursos/solicitudes/${s.id}`}><strong>{s.codigo}</strong></Link>
                    <div className="sub">{s.uo_acronimo}</div>
                  </td>
                  <td data-label="Orden / inmueble">
                    <div>Orden {s.orden_codigo}</div>
                    <div className="sub">{s.inmueble}</div>
                  </td>
                  <td data-label="Almacén">{s.almacen_nombre}</td>
                  <td data-label="Solicitada por">{s.solicitada_por}</td>
                  <td data-label="Total (CUP)">{dinero(s.total)}</td>
                  <td data-label="Estado"><EtiquetaRecurso estado={s.estado} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
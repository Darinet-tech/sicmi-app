import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileCheck2 } from 'lucide-react'
import api, { textoError } from '../../api'
import PaginaModulo from '../../PaginaModulo'
import { ESTADOS_ORDEN } from './estados'

export function EtiquetaOrden({ estado }) {
  return <span className={`etiqueta eo-${estado}`}>{ESTADOS_ORDEN[estado]}</span>
}

export default function OrdenesLista() {
  const [lista, setLista] = useState([])
  const [filtro, setFiltro] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    api
      .get('ordenes/')
      .then((r) => setLista(r.data))
      .catch((e) => setError(textoError(e)))
      .finally(() => setCargando(false))
  }, [])

  const visibles = filtro ? lista.filter((o) => o.estado === filtro) : lista

  return (
    <PaginaModulo
      icono={FileCheck2}
      titulo="Órdenes de trabajo"
      descripcion="Seguimiento de la ejecución, entrega y firma de cada orden."
    >
      <div className="tarjeta">
        <label style={{ marginTop: 0 }}>Filtrar por estado</label>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ maxWidth: 260 }}>
          <option value="">Todos</option>
          {Object.entries(ESTADOS_ORDEN).map(([v, t]) => (
            <option key={v} value={v}>{t}</option>
          ))}
        </select>
      </div>

      {error && <div className="error">{error}</div>}
      {cargando ? (
        <p>Cargando...</p>
      ) : visibles.length === 0 ? (
        <div className="tarjeta">No hay órdenes para mostrar.</div>
      ) : (
        <div className="tabla-wrap sin-marco">
          <table className="tabla-ficha">
            <thead>
              <tr>
                <th>Orden</th>
                <th>Inmueble / local</th>
                <th>Afectación</th>
                <th>Cliente</th>
                <th>Solicitada</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((o) => (
                <tr key={o.id}>
                  <td data-label="Orden">
                    <Link to={`/ordenes/${o.id}`}><strong>{o.codigo}</strong></Link>
                    <div className="sub">{o.tipo_display} · {o.uo_acronimo}</div>
                  </td>
                  <td data-label="Inmueble / local">
                    <div>{o.inmueble_nombre}</div>
                    <div className="sub">{o.local_nombre}</div>
                  </td>
                  <td data-label="Afectación">{o.afectacion}</td>
                  <td data-label="Cliente">{o.cliente_nombre}</td>
                  <td data-label="Solicitada">{new Date(o.fecha_solicitud + 'T00:00:00').toLocaleDateString('es')}</td>
                  <td data-label="Estado"><EtiquetaOrden estado={o.estado} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PaginaModulo>
  )
}
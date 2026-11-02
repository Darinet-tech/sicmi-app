import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CalendarRange, Lock } from 'lucide-react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { MODULOS, tieneAcceso } from '../../modulos'
import PaginaModulo from '../../PaginaModulo'
import { ESTADOS_PLAN, dineroMcup } from './estados'

export default function PlanLista() {
  const { usuario } = useAuth()
  const navigate = useNavigate()
  const modulo = MODULOS.find((m) => m.id === 'plan')
  const puedeCrear = usuario.rol === 'ESPECIALISTA'

  const [lista, setLista] = useState([])
  const [anio, setAnio] = useState(new Date().getFullYear() + 1)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    api
      .get('planes/')
      .then((r) => setLista(r.data))
      .catch((e) => setError(textoError(e)))
      .finally(() => setCargando(false))
  }, [])

  if (!modulo || !tieneAcceso(modulo, usuario.rol)) {
    return (
      <PaginaModulo icono={Lock} titulo="Plan anual preventivo">
        <div className="aviso">Su rol no tiene acceso a este módulo.</div>
      </PaginaModulo>
    )
  }

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      const r = await api.post('planes/', { anio: Number(anio) })
      navigate(`/plan/${r.data.id}`)
    } catch (err) {
      setError(textoError(err))
    }
  }

  return (
    <PaginaModulo
      icono={CalendarRange}
      titulo="Plan anual preventivo"
      descripcion="Planificación del mantenimiento preventivo con medios propios, cronograma y aprobación."
    >
      {puedeCrear && (
        <form className="tarjeta" onSubmit={crear}>
          <h3>Nuevo plan anual</h3>
          <p style={{ marginTop: 0, color: 'var(--gris)' }}>
            El plan de un año se elabora durante el año anterior: la propuesta en el primer trimestre y la
            nominalización por obras cuando llegan las cifras del Área Rectora, en el cuarto.
          </p>
          <div className="agregar-miembro" style={{ marginTop: 0, maxWidth: 360 }}>
            <input type="number" min="2000" max="2100" value={anio} onChange={(e) => setAnio(e.target.value)} required />
            <button className="btn btn-verde">Crear plan</button>
          </div>
        </form>
      )}

      {error && <div className="error">{error}</div>}
      {cargando ? (
        <p>Cargando...</p>
      ) : lista.length === 0 ? (
        <div className="tarjeta">Todavía no hay planes.</div>
      ) : (
        <div className="tabla-wrap sin-marco">
          <table className="tabla-ficha">
            <thead>
              <tr><th>Plan</th><th>Obras (medios propios)</th><th>Acciones</th><th>Valor (MCUP)</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {lista.map((p) => (
                <tr key={p.id}>
                  <td data-label="Plan">
                    <Link to={`/plan/${p.id}`}><strong>Plan {p.anio}</strong></Link>
                    <div className="sub">{p.uo_acronimo}</div>
                  </td>
                  <td data-label="Obras">{p.num_obras}</td>
                  <td data-label="Acciones">{p.total_acciones}</td>
                  <td data-label="Valor (MCUP)">{dineroMcup(p.valor_mcup)}</td>
                  <td data-label="Estado"><span className={`etiqueta ep-${p.estado}`}>{ESTADOS_PLAN[p.estado]}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PaginaModulo>
  )
}
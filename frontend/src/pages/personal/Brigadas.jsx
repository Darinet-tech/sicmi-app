import { useEffect, useState } from 'react'
import { UserMinus, UserPlus } from 'lucide-react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'

export default function Brigadas() {
  const { usuario } = useAuth()
  const puedeEditar = usuario.rol === 'ESPECIALISTA'

  const [brigadas, setBrigadas] = useState([])
  const [trabajadores, setTrabajadores] = useState([])
  const [nombre, setNombre] = useState('')
  const [elegido, setElegido] = useState({}) // id de brigada -> id de trabajador a agregar
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.get('brigadas/'), api.get('trabajadores/')])
      .then(([b, t]) => {
        setBrigadas(b.data)
        setTrabajadores(t.data)
      })
      .catch((e) => setError(textoError(e)))
  }, [])

  // Trabajadores activos que todavía no están en ninguna brigada
  const ocupados = new Set(brigadas.flatMap((b) => b.miembros.map((m) => m.id)))
  const libres = trabajadores.filter((t) => t.activo && !ocupados.has(t.id))
  const activos = trabajadores.filter((t) => t.activo)

  const reemplazar = (b) => setBrigadas(brigadas.map((x) => (x.id === b.id ? b : x)))

  async function ejecutar(peticion) {
    setError('')
    try {
      await peticion()
    } catch (e) {
      setError(textoError(e))
    }
  }

  const crear = (e) => {
    e.preventDefault()
    ejecutar(async () => {
      const r = await api.post('brigadas/', { nombre })
      setBrigadas([...brigadas, r.data])
      setNombre('')
    })
  }

  const agregar = (b) =>
    ejecutar(async () => {
      if (!elegido[b.id]) return
      const r = await api.post(`brigadas/${b.id}/agregar_miembro/`, { trabajador: Number(elegido[b.id]) })
      reemplazar(r.data)
      setElegido({ ...elegido, [b.id]: '' })
    })

  const quitar = (b, idTrabajador) =>
    ejecutar(async () => {
      const r = await api.post(`brigadas/${b.id}/quitar_miembro/`, { trabajador: idTrabajador })
      reemplazar(r.data)
    })

  const cambiarJefe = (b, valor) =>
    ejecutar(async () => {
      const r = await api.patch(`brigadas/${b.id}/`, { jefe: valor ? Number(valor) : null })
      reemplazar(r.data)
    })

  return (
    <>
      {puedeEditar && (
        <form className="tarjeta" onSubmit={crear}>
          <h3>Nueva brigada</h3>
          <label style={{ marginTop: 0 }}>Nombre de la brigada</label>
          <input type="text" value={nombre} required onChange={(e) => setNombre(e.target.value)} />
          <div className="fila-botones">
            <button className="btn btn-verde">Crear brigada</button>
          </div>
        </form>
      )}

      {error && <div className="error">{error}</div>}
      {brigadas.length === 0 && <div className="tarjeta">No hay brigadas creadas.</div>}

      <div className="brigadas">
        {brigadas.map((b) => (
          <div key={b.id} className="tarjeta">
            <h3>
              {b.nombre}
              {usuario.rol === 'CENTRAL' && <small style={{ color: 'var(--gris)' }}> · {b.uo_acronimo}</small>}
            </h3>

            <label style={{ marginTop: 0 }}>Jefe de brigada</label>
            {puedeEditar ? (
              <select value={b.jefe || ''} onChange={(e) => cambiarJefe(b, e.target.value)}>
                <option value="">-- Sin asignar --</option>
                {activos.map((t) => (
                  <option key={t.id} value={t.id}>{t.nombre}</option>
                ))}
              </select>
            ) : (
              <div>{b.jefe_nombre || 'Sin asignar'}</div>
            )}

            <label>Miembros ({b.miembros.length})</label>
            {b.miembros.length === 0 ? (
              <div style={{ color: 'var(--gris)' }}>Sin miembros.</div>
            ) : (
              <ul className="miembros">
                {b.miembros.map((m) => (
                  <li key={m.id}>
                    <span>{m.nombre}<small>{m.cargo}</small></span>
                    {puedeEditar && (
                      <button className="btn-icono-gris" title="Quitar de la brigada" onClick={() => quitar(b, m.id)}>
                        <UserMinus size={16} />
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}

            {puedeEditar && (
              <div className="agregar-miembro">
                <select value={elegido[b.id] || ''} onChange={(e) => setElegido({ ...elegido, [b.id]: e.target.value })}>
                  <option value="">-- Agregar trabajador --</option>
                  {libres.map((t) => (
                    <option key={t.id} value={t.id}>{t.nombre}</option>
                  ))}
                </select>
                <button className="btn btn-verde" onClick={() => agregar(b)} title="Agregar">
                  <UserPlus size={16} />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  )
}
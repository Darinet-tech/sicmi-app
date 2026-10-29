import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'

export default function Trabajadores() {
  const { usuario } = useAuth()
  const puedeEditar = usuario.rol === 'ESPECIALISTA'

  const [lista, setLista] = useState([])
  const [nuevo, setNuevo] = useState({ nombre: '', cargo: '' })
  const [editando, setEditando] = useState(null)
  const [verInactivos, setVerInactivos] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('trabajadores/').then((r) => setLista(r.data)).catch((e) => setError(textoError(e)))
  }, [])

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      const r = await api.post('trabajadores/', nuevo)
      setLista([...lista, r.data].sort((a, b) => a.nombre.localeCompare(b.nombre)))
      setNuevo({ nombre: '', cargo: '' })
    } catch (err) {
      setError(textoError(err))
    }
  }

  async function guardarEdicion() {
    setError('')
    try {
      const r = await api.patch(`trabajadores/${editando.id}/`, {
        nombre: editando.nombre,
        cargo: editando.cargo,
      })
      setLista(lista.map((t) => (t.id === r.data.id ? r.data : t)))
      setEditando(null)
    } catch (err) {
      setError(textoError(err))
    }
  }

  async function alternar(t) {
    setError('')
    try {
      const r = await api.patch(`trabajadores/${t.id}/`, { activo: !t.activo })
      setLista(lista.map((x) => (x.id === r.data.id ? r.data : x)))
    } catch (err) {
      setError(textoError(err))
    }
  }

  const visibles = lista.filter((t) => verInactivos || t.activo)

  return (
    <>
      {puedeEditar && (
        <form className="tarjeta" onSubmit={crear}>
          <h3>Agregar trabajador</h3>
          <div className="dos-columnas">
            <div>
              <label style={{ marginTop: 0 }}>Nombre y apellidos</label>
              <input type="text" value={nuevo.nombre} required
                onChange={(e) => setNuevo({ ...nuevo, nombre: e.target.value })} />
            </div>
            <div>
              <label style={{ marginTop: 0 }}>Cargo</label>
              <input type="text" value={nuevo.cargo}
                onChange={(e) => setNuevo({ ...nuevo, cargo: e.target.value })} />
            </div>
          </div>
          <div className="fila-botones">
            <button className="btn btn-verde">Agregar</button>
          </div>
        </form>
      )}

      {error && <div className="error">{error}</div>}

      <label style={{ marginTop: 0, fontWeight: 400 }}>
        <input type="checkbox" checked={verInactivos} onChange={(e) => setVerInactivos(e.target.checked)} />{' '}
        Mostrar también los inactivos
      </label>

      <div className="tabla-wrap" style={{ marginTop: '0.75rem' }}>
        <table>
          <thead>
            <tr>
              {usuario.rol === 'CENTRAL' && <th>UO</th>}
              <th>Nombre</th>
              <th>Cargo</th>
              <th>Estado</th>
              {puedeEditar && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {visibles.map((t) => (
              <tr key={t.id} style={{ opacity: t.activo ? 1 : 0.55 }}>
                {usuario.rol === 'CENTRAL' && <td>{t.uo_acronimo}</td>}
                {editando?.id === t.id ? (
                  <>
                    <td><input type="text" value={editando.nombre}
                      onChange={(e) => setEditando({ ...editando, nombre: e.target.value })} /></td>
                    <td><input type="text" value={editando.cargo}
                      onChange={(e) => setEditando({ ...editando, cargo: e.target.value })} /></td>
                    <td />
                    <td>
                      <button className="btn btn-verde" onClick={guardarEdicion}>Guardar</button>{' '}
                      <button className="btn btn-gris" onClick={() => setEditando(null)}>Cancelar</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{t.nombre}</td>
                    <td>{t.cargo}</td>
                    <td>
                      <span className={`etiqueta ${t.activo ? 'estado-CERRADA' : 'estado-CANCELADA'}`}>
                        {t.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    {puedeEditar && (
                      <td>
                        <button className="btn btn-gris" onClick={() => setEditando({ ...t })}>Editar</button>{' '}
                        <button className="btn btn-gris" onClick={() => alternar(t)}>
                          {t.activo ? 'Desactivar' : 'Activar'}
                        </button>
                      </td>
                    )}
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
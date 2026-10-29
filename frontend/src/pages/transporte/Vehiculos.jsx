import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'

const VACIO = { chapa: '', tipo: '', descripcion: '' }

export default function Vehiculos() {
  const { usuario } = useAuth()
  const puedeEditar = usuario.rol === 'ESPECIALISTA'

  const [lista, setLista] = useState([])
  const [nuevo, setNuevo] = useState(VACIO)
  const [editando, setEditando] = useState(null)
  const [verInactivos, setVerInactivos] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('vehiculos/').then((r) => setLista(r.data)).catch((e) => setError(textoError(e)))
  }, [])

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      const r = await api.post('vehiculos/', nuevo)
      setLista([...lista, r.data].sort((a, b) => a.chapa.localeCompare(b.chapa)))
      setNuevo(VACIO)
    } catch (err) {
      setError(textoError(err))
    }
  }

  async function guardarEdicion() {
    setError('')
    try {
      const { id, chapa, tipo, descripcion } = editando
      const r = await api.patch(`vehiculos/${id}/`, { chapa, tipo, descripcion })
      setLista(lista.map((v) => (v.id === r.data.id ? r.data : v)))
      setEditando(null)
    } catch (err) {
      setError(textoError(err))
    }
  }

  async function alternar(v) {
    setError('')
    try {
      const r = await api.patch(`vehiculos/${v.id}/`, { activo: !v.activo })
      setLista(lista.map((x) => (x.id === r.data.id ? r.data : x)))
    } catch (err) {
      setError(textoError(err))
    }
  }

  const visibles = lista.filter((v) => verInactivos || v.activo)

  return (
    <>
      {puedeEditar && (
        <form className="tarjeta" onSubmit={crear}>
          <h3>Agregar vehículo</h3>
          <div className="dos-columnas">
            <div>
              <label style={{ marginTop: 0 }}>Chapa</label>
              <input type="text" value={nuevo.chapa} required
                onChange={(e) => setNuevo({ ...nuevo, chapa: e.target.value })} />
            </div>
            <div>
              <label style={{ marginTop: 0 }}>Tipo (camioneta, camión, moto...)</label>
              <input type="text" value={nuevo.tipo}
                onChange={(e) => setNuevo({ ...nuevo, tipo: e.target.value })} />
            </div>
          </div>
          <label>Descripción (marca, modelo...)</label>
          <input type="text" value={nuevo.descripcion}
            onChange={(e) => setNuevo({ ...nuevo, descripcion: e.target.value })} />
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
              <th>Chapa</th>
              <th>Tipo</th>
              <th>Descripción</th>
              <th>Estado</th>
              {puedeEditar && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {visibles.map((v) => (
              <tr key={v.id} style={{ opacity: v.activo ? 1 : 0.55 }}>
                {usuario.rol === 'CENTRAL' && <td>{v.uo_acronimo}</td>}
                {editando?.id === v.id ? (
                  <>
                    <td><input type="text" value={editando.chapa}
                      onChange={(e) => setEditando({ ...editando, chapa: e.target.value })} /></td>
                    <td><input type="text" value={editando.tipo}
                      onChange={(e) => setEditando({ ...editando, tipo: e.target.value })} /></td>
                    <td><input type="text" value={editando.descripcion}
                      onChange={(e) => setEditando({ ...editando, descripcion: e.target.value })} /></td>
                    <td />
                    <td>
                      <button className="btn btn-verde" onClick={guardarEdicion}>Guardar</button>{' '}
                      <button className="btn btn-gris" onClick={() => setEditando(null)}>Cancelar</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td><strong>{v.chapa}</strong></td>
                    <td>{v.tipo}</td>
                    <td>{v.descripcion}</td>
                    <td>
                      <span className={`etiqueta ${v.activo ? 'estado-CERRADA' : 'estado-CANCELADA'}`}>
                        {v.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    {puedeEditar && (
                      <td>
                        <button className="btn btn-gris" onClick={() => setEditando({ ...v })}>Editar</button>{' '}
                        <button className="btn btn-gris" onClick={() => alternar(v)}>
                          {v.activo ? 'Desactivar' : 'Activar'}
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
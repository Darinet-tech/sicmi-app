import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { ESTADOS_VEHICULO } from './estados'

const VACIO = { chapa: '', tipo: '', descripcion: '' }

function hoy() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
}

export default function Vehiculos() {
  const { usuario } = useAuth()
  const puedeEditar = usuario.rol === 'ESPECIALISTA'

  const [lista, setLista] = useState([])
  const [estados, setEstados] = useState({}) // id del vehículo -> {estado, motivo, heredado, sucio}
  const [nuevo, setNuevo] = useState(VACIO)
  const [editando, setEditando] = useState(null)
  const [verInactivos, setVerInactivos] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  useEffect(() => {
    Promise.all([api.get('vehiculos/'), api.get('parte-transporte/', { params: { fecha: hoy() } })])
      .then(([v, p]) => {
        setLista(v.data)
        const mapa = {}
        p.data.registros.forEach((r) => {
          mapa[r.vehiculo] = { estado: r.estado, motivo: r.motivo, heredado: r.heredado, sucio: false }
        })
        setEstados(mapa)
      })
      .catch((e) => setError(textoError(e)))
  }, [])

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      const r = await api.post('vehiculos/', nuevo)
      setLista([...lista, r.data].sort((a, b) => a.chapa.localeCompare(b.chapa)))
      setEstados((s) => ({ ...s, [r.data.id]: { estado: 'DISPONIBLE', motivo: '', heredado: true, sucio: false } }))
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
      if (r.data.activo) {
        setEstados((s) => ({ ...s, [v.id]: s[v.id] || { estado: 'DISPONIBLE', motivo: '', heredado: true, sucio: false } }))
      }
    } catch (err) {
      setError(textoError(err))
    }
  }

  function cambiarEstado(id, campo, valor) {
    setOk('')
    setEstados((s) => ({ ...s, [id]: { ...s[id], [campo]: valor, sucio: true } }))
  }

  async function guardarEstado(v) {
    const e = estados[v.id]
    setError('')
    setOk('')
    if (e.estado === 'OTRAS' && !e.motivo.trim()) {
      return setError(`Indique el motivo de la paralización del vehículo ${v.chapa}.`)
    }
    try {
      await api.post('parte-transporte/', {
        fecha: hoy(),
        registros: [{ vehiculo: v.id, estado: e.estado, motivo: e.motivo }],
      })
      setEstados((s) => ({ ...s, [v.id]: { ...s[v.id], sucio: false, heredado: false } }))
      setOk(`Estado de ${v.chapa} guardado para hoy.`)
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
      {ok && <div className="exito">{ok}</div>}

      <label style={{ marginTop: 0, fontWeight: 400 }}>
        <input type="checkbox" checked={verInactivos} onChange={(e) => setVerInactivos(e.target.checked)} />{' '}
        Mostrar también los inactivos
      </label>

      <div className="tabla-wrap sin-marco" style={{ marginTop: '0.75rem' }}>
        <table className="tabla-ficha">
          <thead>
            <tr>
              {usuario.rol === 'CENTRAL' && <th>UO</th>}
              <th>Chapa</th>
              <th>Vehículo</th>
              <th>Estado de hoy</th>
              <th>Activo</th>
              {puedeEditar && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {visibles.map((v) => {
              const e = estados[v.id]
              const enEdicion = editando?.id === v.id
              return (
                <tr key={v.id} style={{ opacity: v.activo ? 1 : 0.55 }}>
                  {usuario.rol === 'CENTRAL' && <td data-label="UO">{v.uo_acronimo}</td>}
                  {enEdicion ? (
                    <>
                      <td data-label="Chapa">
                        <input type="text" value={editando.chapa}
                          onChange={(ev) => setEditando({ ...editando, chapa: ev.target.value })} />
                      </td>
                      <td data-label="Vehículo">
                        <input type="text" placeholder="Tipo" value={editando.tipo}
                          onChange={(ev) => setEditando({ ...editando, tipo: ev.target.value })} />
                        <input type="text" placeholder="Descripción" value={editando.descripcion}
                          onChange={(ev) => setEditando({ ...editando, descripcion: ev.target.value })}
                          style={{ marginTop: 6 }} />
                      </td>
                      <td data-label="Estado de hoy" />
                      <td data-label="Activo" />
                      <td data-label="Acciones">
                        <div className="acciones-fila">
                          <button className="btn btn-verde" onClick={guardarEdicion}>Guardar</button>
                          <button className="btn btn-gris" onClick={() => setEditando(null)}>Cancelar</button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td data-label="Chapa"><strong>{v.chapa}</strong></td>
                      <td data-label="Vehículo">{[v.tipo, v.descripcion].filter(Boolean).join(' · ')}</td>
                      <td data-label="Estado de hoy">
                        {!v.activo || !e ? (
                          '—'
                        ) : puedeEditar ? (
                          <div className="estado-edit">
                            <select value={e.estado} onChange={(ev) => cambiarEstado(v.id, 'estado', ev.target.value)}>
                              {Object.entries(ESTADOS_VEHICULO).map(([k, t]) => (
                                <option key={k} value={k}>{t}</option>
                              ))}
                            </select>
                            {e.estado !== 'DISPONIBLE' && (
                              <input
                                type="text" value={e.motivo} maxLength={200}
                                placeholder={e.estado === 'OTRAS' ? 'Motivo (obligatorio)' : 'Observación (opcional)'}
                                onChange={(ev) => cambiarEstado(v.id, 'motivo', ev.target.value)}
                              />
                            )}
                            {(e.sucio || e.heredado) && (
                              <button className="btn btn-verde" onClick={() => guardarEstado(v)}>
                                {e.sucio ? 'Guardar' : 'Confirmar'}
                              </button>
                            )}
                          </div>
                        ) : (
                          <>
                            <span className={`etiqueta v-${e.estado}`}>{ESTADOS_VEHICULO[e.estado]}</span>
                            {e.motivo && <div className="sub">{e.motivo}</div>}
                          </>
                        )}
                      </td>
                      <td data-label="Activo">
                        <span className={`etiqueta ${v.activo ? 'estado-CERRADA' : 'estado-CANCELADA'}`}>
                          {v.activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      {puedeEditar && (
                        <td data-label="Acciones">
                          <div className="acciones-fila">
                            <button className="btn btn-gris" onClick={() => setEditando({ ...v })}>Editar</button>
                            <button className="btn btn-gris" onClick={() => alternar(v)}>
                              {v.activo ? 'Desactivar' : 'Activar'}
                            </button>
                          </div>
                        </td>
                      )}
                    </>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}
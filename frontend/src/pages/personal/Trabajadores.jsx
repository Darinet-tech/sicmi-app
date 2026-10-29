import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import FormTrabajador from './FormTrabajador'

export default function Trabajadores() {
  const { usuario } = useAuth()
  const puedeEditar = usuario.rol === 'ESPECIALISTA'

  const [lista, setLista] = useState([])
  const [form, setForm] = useState(null) // null = cerrado, {} = nuevo, objeto = edición
  const [buscar, setBuscar] = useState('')
  const [verInactivos, setVerInactivos] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('trabajadores/').then((r) => setLista(r.data)).catch((e) => setError(textoError(e)))
  }, [])

  function guardado(t) {
    setLista((prev) =>
      prev.some((x) => x.id === t.id)
        ? prev.map((x) => (x.id === t.id ? t : x))
        : [...prev, t].sort((a, b) => a.nombre.localeCompare(b.nombre))
    )
    setForm(null)
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

  const q = buscar.toLowerCase()
  const visibles = lista.filter(
    (t) => (verInactivos || t.activo) && `${t.codigo} ${t.nombre}`.toLowerCase().includes(q)
  )

  return (
    <>
      {puedeEditar && !form && (
        <div className="fila-botones" style={{ marginTop: 0, marginBottom: '1rem' }}>
          <button className="btn btn-verde" onClick={() => setForm({})}>+ Nuevo trabajador</button>
        </div>
      )}

      {form && (
        <FormTrabajador
          key={form.id || 'nuevo'}
          inicial={form}
          onGuardado={guardado}
          onCancelar={() => setForm(null)}
        />
      )}

      {error && <div className="error">{error}</div>}

      <div className="tarjeta">
        <div className="dos-columnas">
          <div>
            <label style={{ marginTop: 0 }}>Buscar por código o nombre</label>
            <input type="text" value={buscar} onChange={(e) => setBuscar(e.target.value)} />
          </div>
          <label style={{ fontWeight: 400, alignSelf: 'end' }}>
            <input type="checkbox" checked={verInactivos} onChange={(e) => setVerInactivos(e.target.checked)} />{' '}
            Mostrar también los inactivos
          </label>
        </div>
      </div>

      <div className="tabla-wrap">
        <table>
          <thead>
            <tr>
              {usuario.rol === 'CENTRAL' && <th>UO</th>}
              <th>Código</th>
              <th>Nombre</th>
              <th>Cargo</th>
              <th>Cat.</th>
              <th>Departamento</th>
              <th>Estado</th>
              {puedeEditar && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {visibles.map((t) => (
              <tr key={t.id} style={{ opacity: t.activo ? 1 : 0.55 }}>
                {usuario.rol === 'CENTRAL' && <td>{t.uo_acronimo}</td>}
                <td><strong>{t.codigo}</strong></td>
                <td>{t.nombre}</td>
                <td>{t.cargo_display}</td>
                <td>{t.categoria}</td>
                <td>{t.departamento}</td>
                <td>
                  <span className={`etiqueta ${t.activo ? 'estado-CERRADA' : 'estado-CANCELADA'}`}>
                    {t.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                {puedeEditar && (
                  <td>
                    <button className="btn btn-gris" onClick={() => setForm(t)}>Editar</button>{' '}
                    <button className="btn btn-gris" onClick={() => alternar(t)}>
                      {t.activo ? 'Desactivar' : 'Activar'}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
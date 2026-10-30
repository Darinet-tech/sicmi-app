import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import FormTrabajador from './FormTrabajador'

// Muestra "Etiqueta valor" solo si hay valor
const Dato = ({ etq, v }) =>
  v === undefined || v === null || v === '' ? null : (
    <div><span className="sub">{etq}</span> {v}</div>
  )

export default function Trabajadores() {
  const { usuario } = useAuth()
  const puedeEditar = usuario.rol === 'ESPECIALISTA'
  // Estos roles reciben la ficha completa (el servidor decide; esto solo adapta la tabla)
  const completo = usuario.rol === 'ESPECIALISTA' || usuario.rol === 'JEFE_LOGISTICA'

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

      <div className="tabla-wrap sin-marco">
        <table className="tabla-ficha">
          <thead>
            <tr>
              {usuario.rol === 'CENTRAL' && <th>UO</th>}
              <th>Trabajador</th>
              <th>Puesto</th>
              <th>Centros</th>
              {completo && <th>Datos personales</th>}
              {completo && <th>Licencia</th>}
              {completo && <th>Contacto</th>}
              {completo && <th>Salario</th>}
              <th>Estado</th>
              {puedeEditar && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {visibles.map((t) => (
              <tr key={t.id} style={{ opacity: t.activo ? 1 : 0.55 }}>
                {usuario.rol === 'CENTRAL' && <td data-label="UO">{t.uo_acronimo}</td>}
                <td data-label="Trabajador">
                  <strong>{t.codigo}</strong>
                  <div>{t.nombre}</div>
                  <Dato etq="CI" v={t.carnet_identidad} />
                </td>
                <td data-label="Puesto">
                  <div>{t.cargo_display} · Cat. {t.categoria}</div>
                  <Dato etq="Depto." v={t.departamento_nombre} />
                  <Dato etq="Plaza" v={t.numero_plaza} />
                </td>
                <td data-label="Centros">
                  <Dato etq="Principal" v={t.centro_principal_nombre} />
                  <Dato etq="Asociado" v={t.centro_asociado_nombre} />
                </td>
                {completo && (
                  <td data-label="Datos personales">
                    <Dato etq="Nivel" v={t.nivel_escolar_display} />
                    <Dato etq="Dirección" v={t.direccion} />
                  </td>
                )}
                {completo && (
                  <td data-label="Licencia">
                    {t.licencia_conduccion ? (
                      <>
                        <div>Sí · Cat. {t.categoria_licencia}</div>
                        <Dato etq="No." v={t.numero_licencia} />
                      </>
                    ) : (
                      'No'
                    )}
                  </td>
                )}
                {completo && (
                  <td data-label="Contacto">
                    <Dato etq="Móvil" v={t.movil} />
                    <Dato etq="Part." v={t.telefono_particular} />
                    <Dato etq="Ofic." v={t.telefono_oficina} />
                  </td>
                )}
                {completo && (
                  <td data-label="Salario">
                    {t.salario !== undefined &&
                      `$ ${Number(t.salario).toLocaleString('es', { minimumFractionDigits: 2 })}`}
                  </td>
                )}
                <td data-label="Estado">
                  <span className={`etiqueta ${t.activo ? 'estado-CERRADA' : 'estado-CANCELADA'}`}>
                    {t.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                {puedeEditar && (
                  <td data-label="Acciones">
                    <div className="acciones-fila">
                      <button className="btn btn-gris" onClick={() => setForm(t)}>Editar</button>
                      <button className="btn btn-gris" onClick={() => alternar(t)}>
                        {t.activo ? 'Desactivar' : 'Activar'}
                      </button>
                    </div>
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
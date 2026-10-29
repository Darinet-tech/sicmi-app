import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { ESTADOS_VEHICULO } from './estados'

function hoy() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
}

export default function ParteDiario() {
  const { usuario } = useAuth()
  const puedeEditar = usuario.rol === 'ESPECIALISTA'

  const [fecha, setFecha] = useState(hoy())
  const [filas, setFilas] = useState([])
  const [guardado, setGuardado] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  useEffect(() => {
    setCargando(true)
    setError('')
    setOk('')
    api
      .get('parte-transporte/', { params: { fecha } })
      .then((r) => {
        setFilas(r.data.registros)
        setGuardado(r.data.guardado)
      })
      .catch((e) => setError(textoError(e)))
      .finally(() => setCargando(false))
  }, [fecha])

  function cambiar(id, campo, valor) {
    setOk('')
    setFilas(filas.map((f) => (f.vehiculo === id ? { ...f, [campo]: valor } : f)))
  }

  async function guardar() {
    setError('')
    setOk('')
    const sinMotivo = filas.find((f) => f.estado === 'OTRAS' && !f.motivo.trim())
    if (sinMotivo) {
      return setError(`Indique el motivo para el vehículo ${sinMotivo.chapa} (paralizado por otras causas).`)
    }
    setEnviando(true)
    try {
      const registros = filas.map((f) => ({ vehiculo: f.vehiculo, estado: f.estado, motivo: f.motivo }))
      const r = await api.post('parte-transporte/', { fecha, registros })
      setOk(r.data.detalle)
      setGuardado(true)
      setFilas(filas.map((f) => ({ ...f, heredado: false })))
    } catch (e) {
      setError(textoError(e))
    } finally {
      setEnviando(false)
    }
  }

  const resumen = filas.reduce((acc, f) => {
    acc[f.estado] = (acc[f.estado] || 0) + 1
    return acc
  }, {})

  return (
    <>
      <div className="tarjeta">
        <div className="barra" style={{ marginBottom: 0 }}>
          <div>
            <label style={{ marginTop: 0 }}>Fecha</label>
            <input
              type="date"
              value={fecha}
              max={hoy()}
              onChange={(e) => e.target.value && setFecha(e.target.value)}
              style={{ maxWidth: 200 }}
            />
          </div>
          <span className={`etiqueta ${guardado ? 'estado-CERRADA' : 'estado-EN_REVISION'}`}>
            {guardado ? 'Parte guardado' : 'Sin confirmar para esta fecha'}
          </span>
        </div>
      </div>

      <div className="resumen-estados">
        {Object.entries(ESTADOS_VEHICULO).map(([clave, texto]) => (
          <div key={clave} className={`resumen-item v-${clave}`}>
            <b>{resumen[clave] || 0}</b>
            <span>{texto}</span>
          </div>
        ))}
      </div>

      {error && <div className="error">{error}</div>}
      {ok && <div className="exito">{ok}</div>}

      {cargando ? (
        <p>Cargando...</p>
      ) : filas.length === 0 ? (
        <div className="tarjeta">No hay vehículos activos. Agréguelos en la sección Vehículos.</div>
      ) : (
        <>
          {!guardado && (
            <div className="aviso">
              Las filas amarillas muestran el último estado registrado y aún no están confirmadas
              para esta fecha. Revíselas y pulse Guardar.
            </div>
          )}
          <div className="tabla-wrap">
            <table>
              <thead>
                <tr>
                  {usuario.rol === 'CENTRAL' && <th>UO</th>}
                  <th>Chapa</th>
                  <th>Vehículo</th>
                  <th>Estado</th>
                  <th>Motivo / observación</th>
                </tr>
              </thead>
              <tbody>
                {filas.map((f) => (
                  <tr key={f.vehiculo} className={f.heredado ? 'fila-heredada' : ''}>
                    {usuario.rol === 'CENTRAL' && <td>{f.uo}</td>}
                    <td><strong>{f.chapa}</strong></td>
                    <td>{[f.tipo, f.descripcion].filter(Boolean).join(' · ')}</td>
                    <td>
                      {puedeEditar ? (
                        <select value={f.estado} onChange={(e) => cambiar(f.vehiculo, 'estado', e.target.value)}>
                          {Object.entries(ESTADOS_VEHICULO).map(([v, t]) => (
                            <option key={v} value={v}>{t}</option>
                          ))}
                        </select>
                      ) : (
                        <span className={`etiqueta v-${f.estado}`}>{ESTADOS_VEHICULO[f.estado]}</span>
                      )}
                    </td>
                    <td>
                      {puedeEditar ? (
                        <input
                          type="text"
                          value={f.motivo}
                          maxLength={200}
                          placeholder={f.estado === 'OTRAS' ? 'Obligatorio: indique la causa' : ''}
                          onChange={(e) => cambiar(f.vehiculo, 'motivo', e.target.value)}
                        />
                      ) : (
                        f.motivo
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {puedeEditar && (
            <div className="fila-botones">
              <button className="btn btn-verde" onClick={guardar} disabled={enviando}>
                {enviando ? 'Guardando...' : 'Guardar parte de transporte'}
              </button>
            </div>
          )}
        </>
      )}
    </>
  )
}
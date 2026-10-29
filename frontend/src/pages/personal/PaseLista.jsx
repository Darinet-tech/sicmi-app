import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { ESTADOS_TRABAJADOR } from './estados'

// Fecha de hoy en formato AAAA-MM-DD, según la hora local
function hoy() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
}

export default function PaseLista() {
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
      .get('pase-lista/', { params: { fecha } })
      .then((r) => {
        setFilas(r.data.registros)
        setGuardado(r.data.guardado)
      })
      .catch((e) => setError(textoError(e)))
      .finally(() => setCargando(false))
  }, [fecha])

  function cambiar(id, campo, valor) {
    setOk('')
    setFilas(filas.map((f) => (f.trabajador === id ? { ...f, [campo]: valor } : f)))
  }

  async function guardar() {
    setError('')
    setOk('')
    setEnviando(true)
    try {
      const registros = filas.map((f) => ({
        trabajador: f.trabajador,
        estado: f.estado,
        observacion: f.observacion,
      }))
      const r = await api.post('pase-lista/', { fecha, registros })
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
            {guardado ? 'Pase de lista guardado' : 'Sin confirmar para esta fecha'}
          </span>
        </div>
      </div>

      <div className="resumen-estados">
        {Object.entries(ESTADOS_TRABAJADOR).map(([clave, texto]) => (
          <div key={clave} className={`resumen-item t-${clave}`}>
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
        <div className="tarjeta">No hay trabajadores activos. Agréguelos en la sección Trabajadores.</div>
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
                  <th>Trabajador</th>
                  <th>Cargo</th>
                  <th>Estado</th>
                  <th>Observación</th>
                </tr>
              </thead>
              <tbody>
                {filas.map((f) => (
                  <tr key={f.trabajador} className={f.heredado ? 'fila-heredada' : ''}>
                    {usuario.rol === 'CENTRAL' && <td>{f.uo}</td>}
                    <td>{f.nombre}</td>
                    <td>{f.cargo}</td>
                    <td>
                      {puedeEditar ? (
                        <select
                          value={f.estado}
                          onChange={(e) => cambiar(f.trabajador, 'estado', e.target.value)}
                        >
                          {Object.entries(ESTADOS_TRABAJADOR).map(([v, t]) => (
                            <option key={v} value={v}>{t}</option>
                          ))}
                        </select>
                      ) : (
                        <span className={`etiqueta t-${f.estado}`}>{ESTADOS_TRABAJADOR[f.estado]}</span>
                      )}
                    </td>
                    <td>
                      {puedeEditar ? (
                        <input
                          type="text"
                          value={f.observacion}
                          maxLength={200}
                          onChange={(e) => cambiar(f.trabajador, 'observacion', e.target.value)}
                        />
                      ) : (
                        f.observacion
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
                {enviando ? 'Guardando...' : 'Guardar pase de lista'}
              </button>
            </div>
          )}
        </>
      )}
    </>
  )
}
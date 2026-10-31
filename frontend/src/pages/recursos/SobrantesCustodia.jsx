import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { useAuth } from '../../AuthContext'
import { dinero } from './estados'

export default function SobrantesCustodia() {
  const { usuario } = useAuth()
  const puedeAsignar = usuario.rol === 'ESPECIALISTA' || usuario.rol === 'JEFE_BRIGADA'

  const [lista, setLista] = useState([])
  const [ordenes, setOrdenes] = useState([])
  const [elegida, setElegida] = useState({}) // id del sobrante -> id de la orden
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  function cargar() {
    Promise.all([api.get('sobrantes-custodia/'), api.get('ordenes/')])
      .then(([s, o]) => {
        setLista(s.data)
        setOrdenes(o.data.filter((x) => ['REGISTRADA', 'EN_EJECUCION'].includes(x.estado)))
      })
      .catch((e) => setError(textoError(e)))
  }
  useEffect(cargar, [])

  async function asignar(s) {
    setError('')
    setOk('')
    try {
      const r = await api.post(`sobrantes-custodia/${s.id}/asignar/`, { orden: Number(elegida[s.id]) })
      setOk(r.data.detalle)
      cargar()
    } catch (e) {
      setError(textoError(e))
    }
  }

  const pendientes = lista.filter((s) => !s.orden_destino)
  const usados = lista.filter((s) => s.orden_destino)

  return (
    <>
      {error && <div className="error">{error}</div>}
      {ok && <div className="exito">{ok}</div>}

      <h3 className="seccion-titulo" style={{ marginTop: 0 }}>En custodia, pendientes de usar</h3>
      {pendientes.length === 0 ? (
        <div className="tarjeta">No hay material en custodia.</div>
      ) : (
        <div className="tabla-wrap">
          <table>
            <thead>
              <tr><th>Material</th><th>Cantidad</th><th>Valor (CUP)</th><th>Origen</th>{puedeAsignar && <th>Usar en la orden</th>}</tr>
            </thead>
            <tbody>
              {pendientes.map((s) => (
                <tr key={s.id}>
                  <td>{s.codigo_sap} · {s.descripcion}</td>
                  <td>{s.cantidad} {s.um}</td>
                  <td>{dinero(s.importe)}</td>
                  <td>Orden {s.orden_origen}<div className="sub">Vale {s.vale}</div></td>
                  {puedeAsignar && (
                    <td style={{ minWidth: 240 }}>
                      <div className="agregar-miembro" style={{ marginTop: 0 }}>
                        <select value={elegida[s.id] || ''} onChange={(e) => setElegida({ ...elegida, [s.id]: e.target.value })}>
                          <option value="">-- Seleccione --</option>
                          {ordenes.filter((o) => o.codigo !== s.orden_origen).map((o) => (
                            <option key={o.id} value={o.id}>{o.codigo} · {o.inmueble_nombre}</option>
                          ))}
                        </select>
                        <button className="btn btn-verde" disabled={!elegida[s.id]} onClick={() => asignar(s)}>Asignar</button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {usados.length > 0 && (
        <>
          <h3 className="seccion-titulo">Ya utilizados en otras órdenes</h3>
          <div className="tabla-wrap">
            <table>
              <thead><tr><th>Material</th><th>Cantidad</th><th>Origen</th><th>Usado en</th></tr></thead>
              <tbody>
                {usados.map((s) => (
                  <tr key={s.id}>
                    <td>{s.codigo_sap} · {s.descripcion}</td>
                    <td>{s.cantidad} {s.um}</td>
                    <td>Orden {s.orden_origen}</td>
                    <td>Orden {s.orden_destino}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  )
}
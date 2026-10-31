import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { dinero } from './estados'

export default function Existencias() {
  const [almacenes, setAlmacenes] = useState([])
  const [almacen, setAlmacen] = useState('')
  const [q, setQ] = useState('')
  const [lista, setLista] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('almacenes/').then((r) => setAlmacenes(r.data)).catch((e) => setError(textoError(e)))
  }, [])

  useEffect(() => {
    const t = setTimeout(() => {
      api
        .get('existencias/', { params: { almacen, q } })
        .then((r) => setLista(r.data))
        .catch((e) => setError(textoError(e)))
    }, 300)
    return () => clearTimeout(t)
  }, [almacen, q])

  return (
    <>
      <div className="tarjeta">
        <div className="dos-columnas">
          <div>
            <label style={{ marginTop: 0 }}>Almacén</label>
            <select value={almacen} onChange={(e) => setAlmacen(e.target.value)}>
              <option value="">Todos</option>
              {almacenes.map((a) => <option key={a.id} value={a.id}>{a.codigo} {a.nombre}</option>)}
            </select>
          </div>
          <div>
            <label style={{ marginTop: 0 }}>Buscar por código o descripción</label>
            <input type="text" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      <div className="tabla-wrap">
        <table>
          <thead>
            <tr><th>Almacén</th><th>Código SAP</th><th>Descripción</th><th>UM</th><th>Libre utilización</th><th>Precio (CUP)</th></tr>
          </thead>
          <tbody>
            {lista.map((e) => (
              <tr key={e.id}>
                <td>{e.almacen}</td>
                <td>{e.codigo_sap}</td>
                <td>{e.descripcion}</td>
                <td>{e.um}</td>
                <td>{e.cantidad_libre}</td>
                <td>{dinero(e.valor_unitario)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <small className="pista">Se muestran hasta 40 resultados. Use la búsqueda para acotar.</small>
    </>
  )
}
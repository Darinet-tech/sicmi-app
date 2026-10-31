import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api, { textoError } from '../../api'
import { dinero } from './estados'

export default function NuevaSolicitudRecursos() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [ordenes, setOrdenes] = useState([])
  const [almacenes, setAlmacenes] = useState([])
  const [orden, setOrden] = useState(params.get('orden') || '')
  const [almacen, setAlmacen] = useState('')
  const [q, setQ] = useState('')
  const [resultados, setResultados] = useState([])
  const [lineas, setLineas] = useState([])
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    Promise.all([api.get('ordenes/'), api.get('almacenes/')])
      .then(([o, a]) => {
        setOrdenes(o.data.filter((x) => ['REGISTRADA', 'EN_EJECUCION'].includes(x.estado)))
        setAlmacenes(a.data)
        if (a.data.length === 1) setAlmacen(String(a.data[0].id))
      })
      .catch((e) => setError(textoError(e)))
  }, [])

  // Búsqueda de materiales con una pequeña espera mientras se escribe
  useEffect(() => {
    if (!almacen || q.trim().length < 2) {
      setResultados([])
      return
    }
    const t = setTimeout(() => {
      api
        .get('existencias/', { params: { almacen, q } })
        .then((r) => setResultados(r.data))
        .catch((e) => setError(textoError(e)))
    }, 300)
    return () => clearTimeout(t)
  }, [almacen, q])

  function cambiarAlmacen(valor) {
    setAlmacen(valor)
    setLineas([]) // las líneas pertenecen al almacén anterior
    setResultados([])
  }

  function agregar(r) {
    if (lineas.some((l) => l.material === r.material)) return
    setLineas([...lineas, { ...r, cantidad: '' }])
  }

  const cambiarCantidad = (material, valor) =>
    setLineas(lineas.map((l) => (l.material === material ? { ...l, cantidad: valor } : l)))

  const quitar = (material) => setLineas(lineas.filter((l) => l.material !== material))

  const total = lineas.reduce((s, l) => s + (Number(l.cantidad) || 0) * Number(l.valor_unitario || 0), 0)

  async function enviar(e) {
    e.preventDefault()
    setError('')
    if (lineas.length === 0) return setError('Agregue al menos un material.')
    const mala = lineas.find((l) => !(Number(l.cantidad) > 0) || Number(l.cantidad) > Number(l.cantidad_libre))
    if (mala) {
      return setError(`${mala.codigo_sap}: indique una cantidad mayor que 0 y no mayor que ${mala.cantidad_libre}.`)
    }
    setEnviando(true)
    try {
      const r = await api.post('solicitudes-recursos/', {
        orden: Number(orden),
        almacen: Number(almacen),
        lineas: lineas.map((l) => ({ material: l.material, cantidad: l.cantidad })),
      })
      navigate(`/recursos/solicitudes/${r.data.id}`)
    } catch (err) {
      setError(textoError(err))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="tarjeta" onSubmit={enviar}>
      <h3>Nueva solicitud de recursos</h3>

      <div className="form-grid">
        <div>
          <label style={{ marginTop: 0 }}>Orden de trabajo</label>
          <select value={orden} onChange={(e) => setOrden(e.target.value)} required>
            <option value="">-- Seleccione --</option>
            {ordenes.map((o) => (
              <option key={o.id} value={o.id}>{o.codigo} · {o.inmueble_nombre}</option>
            ))}
          </select>
          {ordenes.length === 0 && <small className="pista">No hay órdenes abiertas.</small>}
        </div>
        <div>
          <label style={{ marginTop: 0 }}>Almacén al que se solicita</label>
          <select value={almacen} onChange={(e) => cambiarAlmacen(e.target.value)} required>
            <option value="">-- Seleccione --</option>
            {almacenes.map((a) => <option key={a.id} value={a.id}>{a.codigo} {a.nombre}</option>)}
          </select>
        </div>
      </div>

      <h4 className="form-seccion">Materiales</h4>
      <label style={{ marginTop: 0 }}>Buscar por código SAP o descripción</label>
      <input type="text" value={q} onChange={(e) => setQ(e.target.value)}
        disabled={!almacen} placeholder={almacen ? 'Escriba al menos 2 letras...' : 'Primero elija el almacén'} />

      {resultados.length > 0 && (
        <ul className="resultados">
          {resultados.map((r) => (
            <li key={r.id}>
              <span>
                <strong>{r.codigo_sap}</strong> · {r.descripcion}
                <small>Hay {r.cantidad_libre} {r.um} · {dinero(r.valor_unitario)} CUP</small>
              </span>
              <button type="button" className="btn btn-gris" onClick={() => agregar(r)}>Agregar</button>
            </li>
          ))}
        </ul>
      )}
      {almacen && q.trim().length >= 2 && resultados.length === 0 && (
        <small className="pista">No hay materiales con existencia que coincidan.</small>
      )}

      {lineas.length > 0 && (
        <div className="tabla-wrap" style={{ marginTop: '1rem' }}>
          <table>
            <thead>
              <tr><th>Código SAP</th><th>Descripción</th><th>UM</th><th>Disponible</th><th>Cantidad</th><th>Importe</th><th /></tr>
            </thead>
            <tbody>
              {lineas.map((l) => (
                <tr key={l.material}>
                  <td>{l.codigo_sap}</td>
                  <td>{l.descripcion}</td>
                  <td>{l.um}</td>
                  <td>{l.cantidad_libre}</td>
                  <td style={{ minWidth: 110 }}>
                    <input type="number" min="0" step="0.001" max={l.cantidad_libre} value={l.cantidad}
                      onChange={(e) => cambiarCantidad(l.material, e.target.value)} required />
                  </td>
                  <td>{dinero((Number(l.cantidad) || 0) * Number(l.valor_unitario || 0))}</td>
                  <td><button type="button" className="btn btn-gris" onClick={() => quitar(l.material)}>Quitar</button></td>
                </tr>
              ))}
              <tr className="total-fila">
                <td colSpan={5}>Total estimado (CUP)</td>
                <td colSpan={2}>{dinero(total)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {error && <div className="error">{error}</div>}
      <div className="fila-botones">
        <button className="btn btn-verde" disabled={enviando}>
          {enviando ? 'Enviando...' : 'Crear solicitud de recursos'}
        </button>
        <Link className="btn btn-gris" to="/recursos/solicitudes">Cancelar</Link>
      </div>
    </form>
  )
}
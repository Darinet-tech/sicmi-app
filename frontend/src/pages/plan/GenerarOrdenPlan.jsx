import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { CalendarRange } from 'lucide-react'
import api, { textoError } from '../../api'
import PaginaModulo from '../../PaginaModulo'
import { MESES } from './estados'

export default function GenerarOrdenPlan() {
  const { id } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const mes = Number(params.get('mes'))

  const [a, setA] = useState(null)
  const [centros, setCentros] = useState([])
  const [areas, setAreas] = useState([])
  const [clientes, setClientes] = useState([])
  const [locales, setLocales] = useState([])
  const [brigadas, setBrigadas] = useState([])
  const [vehiculos, setVehiculos] = useState([])
  const [f, setF] = useState({ centro_costo: '', area_solicitante: '', cliente: '', local: '', brigada: '', vehiculo: '' })
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get(`acciones-plan/${id}/`), api.get('centros-costo/'), api.get('areas/'),
      api.get('plan-clientes/'), api.get('brigadas/'), api.get('vehiculos/'),
    ])
      .then(([x, c, ar, cl, b, v]) => {
        setA(x.data)
        setCentros(c.data)
        setAreas(ar.data)
        setClientes(cl.data)
        setBrigadas(b.data.filter((y) => y.activa))
        setVehiculos(v.data.filter((y) => y.activo))
        api.get('locales/', { params: { inmueble: x.data.inmueble } }).then((r) => setLocales(r.data))
      })
      .catch((e) => setError(textoError(e)))
  }, [id])

  const poner = (campo, valor) => setF({ ...f, [campo]: valor })

  async function generar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)
    try {
      const r = await api.post(`acciones-plan/${id}/generar-orden/`, {
        mes,
        centro_costo: Number(f.centro_costo),
        area_solicitante: Number(f.area_solicitante),
        cliente: Number(f.cliente),
        local: f.local ? Number(f.local) : null,
        brigada: f.brigada ? Number(f.brigada) : null,
        vehiculo: f.vehiculo ? Number(f.vehiculo) : null,
      })
      navigate(`/ordenes/${r.data.id}`)
    } catch (err) {
      setError(textoError(err))
    } finally {
      setEnviando(false)
    }
  }

  if (!a) return error ? <div className="error">{error}</div> : <p>Cargando...</p>

  return (
    <PaginaModulo
      icono={CalendarRange}
      titulo="Generar orden preventiva"
      descripcion={`${a.grupo_nombre} · ${a.inmueble_nombre} · ${MESES[mes - 1] || ''} ${a.anio}`}
      acciones={<Link className="btn btn-gris" to={`/plan/${a.plan}`}>← Volver al plan</Link>}
    >
      <form className="tarjeta" onSubmit={generar}>
        <p style={{ marginTop: 0, color: 'var(--gris)' }}>
          La orden se crea En proceso y sigue el mismo camino que las correctivas: recursos, vale de salida,
          generación, ejecución, conformidad del cliente y firmas.
        </p>
        <div className="form-grid">
          <div>
            <label style={{ marginTop: 0 }}>Centro de costo</label>
            <select value={f.centro_costo} onChange={(e) => poner('centro_costo', e.target.value)} required>
              <option value="">-- Seleccione --</option>
              {centros.map((c) => <option key={c.id} value={c.id}>{c.codigo} {c.nombre}</option>)}
            </select>
          </div>
          <div>
            <label style={{ marginTop: 0 }}>Área solicitante</label>
            <select value={f.area_solicitante} onChange={(e) => poner('area_solicitante', e.target.value)} required>
              <option value="">-- Seleccione --</option>
              {areas.map((x) => <option key={x.id} value={x.id}>{x.nombre}</option>)}
            </select>
          </div>
          <div>
            <label>Cliente (jefe del inmueble, confirma el trabajo)</label>
            <select value={f.cliente} onChange={(e) => poner('cliente', e.target.value)} required>
              <option value="">-- Seleccione --</option>
              {clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre}{c.cargo ? ` · ${c.cargo}` : ''}</option>)}
            </select>
            {clientes.length === 0 && <small className="pista">No hay usuarios con rol Cliente en su UO.</small>}
          </div>
          <div>
            <label>Local (opcional)</label>
            <select value={f.local} onChange={(e) => poner('local', e.target.value)}>
              <option value="">-- Todo el inmueble --</option>
              {locales.map((l) => <option key={l.id} value={l.id}>{l.nombre}</option>)}
            </select>
          </div>
          <div>
            <label>Brigada</label>
            <select value={f.brigada} onChange={(e) => poner('brigada', e.target.value)}>
              <option value="">-- La asignaré después --</option>
              {brigadas.map((b) => <option key={b.id} value={b.id}>{b.nombre}</option>)}
            </select>
          </div>
          <div>
            <label>Vehículo (opcional)</label>
            <select value={f.vehiculo} onChange={(e) => poner('vehiculo', e.target.value)}>
              <option value="">-- Sin vehículo --</option>
              {vehiculos.map((v) => <option key={v.id} value={v.id}>{v.chapa} {v.tipo}</option>)}
            </select>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        <div className="fila-botones">
          <button className="btn btn-verde" disabled={enviando}>{enviando ? 'Creando...' : 'Crear orden en proceso'}</button>
        </div>
      </form>
    </PaginaModulo>
  )
}
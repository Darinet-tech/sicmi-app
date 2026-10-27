import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import api, { textoError } from '../api'

export default function SolicitudForm() {
  const { id } = useParams() // undefined si es una solicitud nueva
  const navigate = useNavigate()
  const editando = Boolean(id)

  const [inmuebles, setInmuebles] = useState([])
  const [centros, setCentros] = useState([])
  const [form, setForm] = useState({
    inmueble: '',
    centro_costo: '',
    area_solicitante: '',
    local: '',
    descripcion: '',
  })
  const [foto, setFoto] = useState(null)
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    api.get('inmuebles/').then((r) => setInmuebles(r.data))
    api.get('centros-costo/').then((r) => setCentros(r.data))
    if (editando) {
      api.get(`solicitudes/${id}/`).then((r) => {
        const s = r.data
        setForm({
          inmueble: s.inmueble,
          centro_costo: s.centro_costo,
          area_solicitante: s.area_solicitante,
          local: s.local,
          descripcion: s.descripcion,
        })
      })
    }
  }, [id, editando])

  function cambiar(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)

    // FormData permite enviar texto y archivo (la foto) juntos
    const datos = new FormData()
    Object.entries(form).forEach(([k, v]) => datos.append(k, v))
    if (foto) datos.append('foto', foto)

    try {
      if (editando) {
        await api.patch(`solicitudes/${id}/`, datos)
        navigate(`/solicitudes/${id}`)
      } else {
        const r = await api.post('solicitudes/', datos)
        navigate(`/solicitudes/${r.data.id}`)
      }
    } catch (err) {
      setError(textoError(err))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="tarjeta">
      <h2>{editando ? `Corregir solicitud #${id}` : 'Nueva solicitud de servicio'}</h2>
      <form onSubmit={enviar}>
        <label>Inmueble</label>
        <select name="inmueble" value={form.inmueble} onChange={cambiar} required>
          <option value="">-- Seleccione --</option>
          {inmuebles.map((i) => (
            <option key={i.id} value={i.id}>{i.denominacion}</option>
          ))}
        </select>

        <label>Centro de costo</label>
        <select name="centro_costo" value={form.centro_costo} onChange={cambiar} required>
          <option value="">-- Seleccione --</option>
          {centros.map((c) => (
            <option key={c.id} value={c.id}>{c.codigo} {c.nombre}</option>
          ))}
        </select>

        <label>Área solicitante (departamento, grupo...)</label>
        <input type="text" name="area_solicitante" value={form.area_solicitante} onChange={cambiar} required />

        <label>Local donde ocurre la incidencia</label>
        <input type="text" name="local" value={form.local} onChange={cambiar} required />

        <label>Descripción de las afectaciones</label>
        <textarea name="descripcion" value={form.descripcion} onChange={cambiar} required />

        <label>Foto de la avería (opcional)</label>
        <input type="file" accept="image/*" onChange={(e) => setFoto(e.target.files[0])} />

        {error && <div className="error">{error}</div>}

        <div className="fila-botones">
          <button className="btn btn-verde" disabled={enviando}>
            {enviando ? 'Guardando...' : editando ? 'Guardar cambios' : 'Enviar solicitud'}
          </button>
          <Link className="btn btn-gris" to={editando ? `/solicitudes/${id}` : '/solicitudes'}>
            Cancelar
          </Link>
        </div>
      </form>
    </div>
  )
}
import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import api, { textoError } from '../api'

const VACIO = {
  inmueble: '', centro_costo: '', area_solicitante: '', local: '',
  afectacion: '', otra_afectacion: '', descripcion: '',
}

export default function SolicitudForm() {
  const { id } = useParams() // undefined si es una solicitud nueva
  const navigate = useNavigate()
  const editando = Boolean(id)

  const [inmuebles, setInmuebles] = useState([])
  const [centros, setCentros] = useState([])
  const [areas, setAreas] = useState([])
  const [afectaciones, setAfectaciones] = useState([])
  const [locales, setLocales] = useState([])
  const [form, setForm] = useState(VACIO)
  const [foto, setFoto] = useState(null)
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  // Catálogos fijos
  useEffect(() => {
    Promise.all([
      api.get('inmuebles/'), api.get('centros-costo/'),
      api.get('areas/'), api.get('grupos-genericos/'),
    ])
      .then(([i, c, a, g]) => {
        setInmuebles(i.data)
        setCentros(c.data)
        setAreas(a.data)
        setAfectaciones(g.data)
      })
      .catch((e) => setError(textoError(e)))

    if (editando) {
      api.get(`solicitudes/${id}/`).then((r) => {
        const s = r.data
        setForm({
          inmueble: s.inmueble,
          centro_costo: s.centro_costo,
          area_solicitante: s.area_solicitante,
          local: s.local,
          afectacion: s.afectacion ? s.afectacion : s.otra_afectacion ? 'OTRA' : '',
          otra_afectacion: s.otra_afectacion || '',
          descripcion: s.descripcion,
        })
      })
    }
  }, [id, editando])

  // Los locales dependen del inmueble elegido
  useEffect(() => {
    if (!form.inmueble) {
      setLocales([])
      return
    }
    api.get('locales/', { params: { inmueble: form.inmueble } }).then((r) => setLocales(r.data))
  }, [form.inmueble])

  function cambiar(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  function cambiarInmueble(e) {
    // Al cambiar de inmueble, el local elegido deja de ser válido
    setForm({ ...form, inmueble: e.target.value, local: '' })
  }

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)

    // FormData permite enviar texto y archivo (la foto) juntos
    const { afectacion, otra_afectacion, ...resto } = form
    const datos = new FormData()
    Object.entries(resto).forEach(([k, v]) => datos.append(k, v))
    if (afectacion === 'OTRA') {
      datos.append('afectacion', '')
      datos.append('otra_afectacion', otra_afectacion)
    } else if (afectacion) {
      datos.append('afectacion', afectacion)
    }
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
        <div className="form-grid">
          <div>
            <label style={{ marginTop: 0 }}>Inmueble</label>
            <select name="inmueble" value={form.inmueble} onChange={cambiarInmueble} required>
              <option value="">-- Seleccione --</option>
              {inmuebles.map((i) => <option key={i.id} value={i.id}>{i.denominacion}</option>)}
            </select>
          </div>

          <div>
            <label style={{ marginTop: 0 }}>Centro de costo</label>
            <select name="centro_costo" value={form.centro_costo} onChange={cambiar} required>
              <option value="">-- Seleccione --</option>
              {centros.map((c) => <option key={c.id} value={c.id}>{c.codigo} {c.nombre}</option>)}
            </select>
          </div>

          <div>
            <label>Área solicitante</label>
            <select name="area_solicitante" value={form.area_solicitante} onChange={cambiar} required>
              <option value="">-- Seleccione --</option>
              {areas.map((a) => <option key={a.id} value={a.id}>{a.nombre}</option>)}
            </select>
            {areas.length === 0 && <small className="pista">No hay áreas registradas. Pida al administrador que las cree.</small>}
          </div>

          <div>
            <label>Local donde ocurre la incidencia</label>
            <select name="local" value={form.local} onChange={cambiar} required disabled={!form.inmueble}>
              <option value="">{form.inmueble ? '-- Seleccione --' : 'Primero elija el inmueble'}</option>
              {locales.map((l) => <option key={l.id} value={l.id}>{l.nombre}</option>)}
            </select>
            {form.inmueble && locales.length === 0 && (
              <small className="pista">Este inmueble no tiene locales registrados.</small>
            )}
          </div>

          <div className="campo-completo">
            <label>Afectación</label>
            <select name="afectacion" value={form.afectacion} onChange={cambiar} required>
              <option value="">-- Seleccione --</option>
              {afectaciones.map((g) => <option key={g.id} value={g.id}>{g.nombre}</option>)}
              <option value="OTRA">Otra afectación (no está en la lista)</option>
            </select>
          </div>

          {form.afectacion === 'OTRA' && (
            <div className="campo-completo">
              <label style={{ marginTop: 0 }}>Indique cuál es la afectación</label>
              <input type="text" name="otra_afectacion" value={form.otra_afectacion}
                onChange={cambiar} maxLength={150} required />
            </div>
          )}
        </div>

        <label>Descripción detallada de las afectaciones</label>
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
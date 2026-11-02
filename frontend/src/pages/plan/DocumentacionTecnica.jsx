import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CalendarRange } from 'lucide-react'
import api, { API_URL, textoError } from '../../api'
import ExportarAnexo from '../../ExportarAnexo'
import PaginaModulo from '../../PaginaModulo'

const FILA = { desperfecto: '', trabajo: '', um: '', cantidad: '' }
const CRO = { plano_no: '', escala: '', fecha: '', proyecto: '', plano: '', elaborado: '', proyectado: '', aprobado: '' }

export default function DocumentacionTecnica() {
  const { id } = useParams()
  const [a, setA] = useState(null)
  const [tt, setTt] = useState(null)
  const [cr, setCr] = useState(null)
  const [cf, setCf] = useState(CRO)
  const [archivo, setArchivo] = useState(null)
  const [clave, setClave] = useState(0)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get(`acciones-plan/${id}/`),
      api.get(`acciones-plan/${id}/tarea-tecnica/`),
      api.get(`acciones-plan/${id}/croquis/`),
    ])
      .then(([x, t, c]) => {
        setA(x.data)
        setTt({ ...t.data, trabajos: t.data.trabajos.length ? t.data.trabajos : [{ ...FILA }] })
        setCr(c.data)
        if (c.data.existe) setCf({ ...CRO, ...c.data, fecha: c.data.fecha || '' })
      })
      .catch((e) => setError(textoError(e)))
  }, [id])

  if (!a || !tt) return error ? <div className="error">{error}</div> : <p>Cargando...</p>

  const puede = a.puede_editar_tecnica
  const ponerFila = (i, campo, valor) =>
    setTt({ ...tt, trabajos: tt.trabajos.map((f, j) => (j === i ? { ...f, [campo]: valor } : f)) })

  async function guardarTt() {
    setError('')
    setOk('')
    setOcupado(true)
    try {
      const r = await api.put(`acciones-plan/${id}/tarea-tecnica/`, {
        descripcion_general: tt.descripcion_general,
        trabajos: tt.trabajos.filter((f) => Object.values(f).some(Boolean)),
        elaborado_nombre: tt.elaborado_nombre,
        elaborado_cargo: tt.elaborado_cargo,
      })
      setTt({ ...r.data, trabajos: r.data.trabajos.length ? r.data.trabajos : [{ ...FILA }] })
      setOk('Tarea técnica guardada.')
    } catch (e) {
      setError(textoError(e))
    } finally {
      setOcupado(false)
    }
  }

  async function guardarCroquis() {
    setError('')
    setOk('')
    setOcupado(true)
    try {
      const datos = new FormData()
      Object.entries(cf).forEach(([k, v]) => { if (CRO[k] !== undefined && v) datos.append(k, v) })
      if (archivo) datos.append('imagen', archivo)
      const r = await api.post(`acciones-plan/${id}/croquis/`, datos)
      setCr(r.data)
      setArchivo(null)
      setClave(clave + 1)
      setOk('Croquis guardado.')
    } catch (e) {
      setError(textoError(e))
    } finally {
      setOcupado(false)
    }
  }

  async function quitarCroquis() {
    if (!window.confirm('¿Quitar el croquis de esta obra?')) return
    try {
      const r = await api.delete(`acciones-plan/${id}/croquis/`)
      setCr(r.data)
      setCf(CRO)
    } catch (e) {
      setError(textoError(e))
    }
  }

  const campoCro = (campo, etiqueta, tipo = 'text') => (
    <div>
      <label style={{ marginTop: 0 }}>{etiqueta}</label>
      <input type={tipo} value={cf[campo] || ''} disabled={!puede}
        onChange={(e) => setCf({ ...cf, [campo]: e.target.value })} />
    </div>
  )

  return (
    <PaginaModulo
      icono={CalendarRange}
      titulo="Documentación técnica de la obra"
      descripcion={`${a.grupo_nombre} · ${a.inmueble_nombre} · Plan ${a.anio}`}
      acciones={<Link className="btn btn-gris" to={`/plan/${a.plan}`}>← Volver al plan</Link>}
    >
      {error && <div className="error">{error}</div>}
      {ok && <div className="exito">{ok}</div>}
      {!puede && <div className="aviso">Solo el Especialista puede editar esta documentación, y únicamente mientras el plan está en elaboración o aprobado.</div>}

      <div className="tarjeta">
        <h3>Anexo 7 · Tarea técnica</h3>
        <label style={{ marginTop: 0 }}>Descripción general del inmueble u objeto de obra</label>
        <textarea value={tt.descripcion_general} disabled={!puede}
          onChange={(e) => setTt({ ...tt, descripcion_general: e.target.value })} />

        <h4 className="form-seccion">Trabajos constructivos a realizar</h4>
        <div className="tabla-wrap">
          <table>
            <thead>
              <tr><th>No</th><th>Desperfectos / ubicación y tipo</th><th>Trabajos a realizar</th><th>UM</th><th>Cantidad</th>{puede && <th />}</tr>
            </thead>
            <tbody>
              {tt.trabajos.map((f, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  {['desperfecto', 'trabajo', 'um', 'cantidad'].map((campo) => (
                    <td key={campo} style={{ minWidth: campo === 'um' || campo === 'cantidad' ? 80 : 180 }}>
                      <input type="text" value={f[campo]} disabled={!puede} maxLength={200}
                        onChange={(e) => ponerFila(i, campo, e.target.value)} />
                    </td>
                  ))}
                  {puede && (
                    <td>
                      <button className="btn btn-gris" onClick={() => setTt({ ...tt, trabajos: tt.trabajos.filter((_, j) => j !== i) })}>
                        Quitar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {puede && (
          <div className="fila-botones">
            <button className="btn btn-gris" onClick={() => setTt({ ...tt, trabajos: [...tt.trabajos, { ...FILA }] })}>
              + Agregar fila
            </button>
          </div>
        )}

        <div className="dos-columnas" style={{ marginTop: '1rem' }}>
          <div>
            <label style={{ marginTop: 0 }}>Elaborado por (nombre y apellidos)</label>
            <input type="text" value={tt.elaborado_nombre} disabled={!puede}
              onChange={(e) => setTt({ ...tt, elaborado_nombre: e.target.value })} />
          </div>
          <div>
            <label style={{ marginTop: 0 }}>Cargo</label>
            <input type="text" value={tt.elaborado_cargo} disabled={!puede}
              onChange={(e) => setTt({ ...tt, elaborado_cargo: e.target.value })} />
          </div>
        </div>
        <div className="fila-botones">
          {puede && <button className="btn btn-verde" disabled={ocupado} onClick={guardarTt}>Guardar tarea técnica</button>}
        </div>
        {tt.existe && (
          <div style={{ marginTop: '1rem' }}>
            <ExportarAnexo titulo="Anexo 7 · Tarea técnica" ruta={`anexos/tarea-tecnica/${id}/`} nombre={`Anexo7-TareaTecnica-${id}`} />
          </div>
        )}
      </div>

      <div className="tarjeta">
        <h3>Anexo 8 · Croquis o plano de la obra</h3>
        {cr?.existe && cr.url && (
          <p>
            <img className="foto" src={`${API_URL}${cr.url}?v=${encodeURIComponent(cr.actualizado)}`} alt="Croquis de la obra" />
          </p>
        )}
        {puede && (
          <>
            <label style={{ marginTop: 0 }}>
              {cr?.existe ? 'Reemplazar la imagen (opcional)' : 'Imagen del croquis (JPG o PNG, máximo 8 MB)'}
            </label>
            <input key={clave} type="file" accept="image/png,image/jpeg"
              onChange={(e) => setArchivo(e.target.files[0] || null)} />
            <small className="pista">Puede fotografiar o escanear el plano a mano y subirlo aquí.</small>
          </>
        )}
        <h4 className="form-seccion">Cajetín del plano</h4>
        <div className="form-grid">
          {campoCro('plano_no', 'Plano No.')}
          {campoCro('escala', 'Escala')}
          {campoCro('fecha', 'Fecha', 'date')}
          {campoCro('proyecto', 'Proyecto')}
          {campoCro('plano', 'Plano (título)')}
          {campoCro('elaborado', 'Elaborado')}
          {campoCro('proyectado', 'Proyectado')}
          {campoCro('aprobado', 'Aprobado')}
        </div>
        {puede && (
          <div className="fila-botones">
            <button className="btn btn-verde" disabled={ocupado} onClick={guardarCroquis}>Guardar croquis</button>
            {cr?.existe && <button className="btn btn-gris" onClick={quitarCroquis}>Quitar croquis</button>}
          </div>
        )}
        {cr?.existe && (
          <div style={{ marginTop: '1rem' }}>
            <ExportarAnexo titulo="Anexo 8 · Croquis o plano" ruta={`anexos/croquis/${id}/`} nombre={`Anexo8-Croquis-${id}`} />
          </div>
        )}
      </div>
    </PaginaModulo>
  )
}
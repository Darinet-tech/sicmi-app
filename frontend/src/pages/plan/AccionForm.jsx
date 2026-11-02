import { useEffect, useState } from 'react'
import api, { textoError } from '../../api'
import { CICLOS, MESES, MESES_ABR, PRIORIDADES, VIAS } from './estados'

export default function AccionForm({ planId, inicial, onGuardado, onCancelar }) {
  const editando = Boolean(inicial?.id)
  const [inmuebles, setInmuebles] = useState([])
  const [grupos, setGrupos] = useState([])
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [f, setF] = useState({
    inmueble: inicial?.inmueble || '',
    grupo: inicial?.grupo || '',
    descripcion: inicial?.descripcion || '',
    via: inicial?.via || 'PROPIOS',
    prioridad: inicial?.prioridad || 4,
    es_compleja: inicial?.es_compleja || false,
    valor_estimado: inicial?.valor_estimado ?? '',
    programacion: inicial?.programacion || {},
  })

  useEffect(() => {
    Promise.all([api.get('inmuebles/'), api.get('grupos-genericos/')])
      .then(([i, g]) => {
        setInmuebles(i.data)
        setGrupos(g.data)
      })
      .catch((e) => setError(textoError(e)))
  }, [])

  const poner = (campo, valor) => setF({ ...f, [campo]: valor })
  const ponerMes = (m, valor) => setF({ ...f, programacion: { ...f.programacion, [m]: valor } })
  const total = Object.values(f.programacion).reduce((s, v) => s + (Number(v) || 0), 0)
  const grupoElegido = grupos.find((g) => String(g.id) === String(f.grupo))

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)
    try {
      const r = editando
        ? await api.patch(`acciones-plan/${inicial.id}/`, f)
        : await api.post('acciones-plan/', { ...f, plan: planId })
      onGuardado(r.data)
    } catch (err) {
      setError(textoError(err))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="tarjeta" onSubmit={enviar}>
      <h3>{editando ? 'Editar obra' : 'Nueva obra del plan'}</h3>
      <div className="form-grid">
        <div>
          <label style={{ marginTop: 0 }}>Inmueble</label>
          <select value={f.inmueble} onChange={(e) => poner('inmueble', e.target.value)} required>
            <option value="">-- Seleccione --</option>
            {inmuebles.map((i) => <option key={i.id} value={i.id}>{i.denominacion}</option>)}
          </select>
        </div>
        <div>
          <label style={{ marginTop: 0 }}>Grupo genérico de acciones</label>
          <select value={f.grupo} onChange={(e) => poner('grupo', e.target.value)} required>
            <option value="">-- Seleccione --</option>
            {grupos.map((g) => <option key={g.id} value={g.id}>{g.numero}. {g.nombre}</option>)}
          </select>
        </div>
        <div>
          <label>Vía de ejecución</label>
          <select value={f.via} onChange={(e) => poner('via', e.target.value)}>
            {Object.entries(VIAS).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </div>
        <div>
          <label>Prioridad</label>
          <select value={f.prioridad} onChange={(e) => poner('prioridad', Number(e.target.value))}>
            {Object.entries(PRIORIDADES).map(([v, t]) => <option key={v} value={v}>{v}. {t}</option>)}
          </select>
        </div>
      </div>

      {grupoElegido && CICLOS[grupoElegido.numero] && <div className="aviso">{CICLOS[grupoElegido.numero]}</div>}

      <label>Descripción de las acciones a realizar</label>
      <textarea value={f.descripcion} onChange={(e) => poner('descripcion', e.target.value)} style={{ minHeight: 80 }} />

      <label style={{ fontWeight: 400 }}>
        <input type="checkbox" checked={f.es_compleja} onChange={(e) => poner('es_compleja', e.target.checked)} />{' '}
        Obra de mantenimiento compleja (requiere Tarea técnica antes de generar sus órdenes)
      </label>

      <h4 className="form-seccion">Cronograma: acciones por mes ({total} en el año)</h4>
      <div className="prog-grid">
        {MESES_ABR.map((l, i) => (
          <div key={i}>
            <small title={MESES[i]}>{MESES[i].slice(0, 3)}</small>
            <input type="number" min="0" max="99" value={f.programacion[i + 1] ?? ''}
              onChange={(e) => ponerMes(i + 1, e.target.value)} />
          </div>
        ))}
      </div>

      <label>Valor estimado (miles de CUP)</label>
      <input type="number" min="0" step="0.001" value={f.valor_estimado}
        onChange={(e) => poner('valor_estimado', e.target.value)} style={{ maxWidth: 220 }} />

      {error && <div className="error">{error}</div>}
      <div className="fila-botones">
        <button className="btn btn-verde" disabled={enviando}>{enviando ? 'Guardando...' : 'Guardar obra'}</button>
        <button type="button" className="btn btn-gris" onClick={onCancelar}>Cancelar</button>
      </div>
    </form>
  )
}
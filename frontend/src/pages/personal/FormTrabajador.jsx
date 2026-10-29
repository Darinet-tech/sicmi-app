import { useState } from 'react'
import api, { textoError } from '../../api'
import { CARGOS, LETRAS, NIVELES } from './opciones'

const VACIO = {
  codigo: '', nombre: '', carnet_identidad: '',
  nivel_escolar: 'DOCE', direccion: '',
  cargo: 'OPERARIO', categoria: 'A', departamento: '',
  centro_principal: '', centro_asociado: '', numero_plaza: '', salario: '',
  licencia_conduccion: false, numero_licencia: '', categoria_licencia: '',
  movil: '', telefono_particular: '', telefono_oficina: '', activo: true,
}

function Campo({ etiqueta, completo, children }) {
  return (
    <div className={completo ? 'campo-completo' : ''}>
      <label style={{ marginTop: 0 }}>{etiqueta}</label>
      {children}
    </div>
  )
}

export default function FormTrabajador({ inicial, onGuardado, onCancelar }) {
  const editando = Boolean(inicial?.id)
  const [f, setF] = useState({ ...VACIO, ...inicial })
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  function poner(campo, valor) {
    setF((a) => {
      const n = { ...a, [campo]: valor }
      // Un Jefe de Departamento solo puede ser categoría A, B o C
      if (n.cargo === 'JEFE_DEPARTAMENTO' && n.categoria === 'D') n.categoria = 'C'
      return n
    })
  }

  const letrasCargo = f.cargo === 'JEFE_DEPARTAMENTO' ? ['A', 'B', 'C'] : LETRAS
  const texto = (campo, extra = {}) => (
    <input type="text" value={f[campo]} onChange={(e) => poner(campo, e.target.value)} {...extra} />
  )

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)
    try {
      const r = editando
        ? await api.patch(`trabajadores/${inicial.id}/`, f)
        : await api.post('trabajadores/', f)
      onGuardado(r.data)
    } catch (err) {
      setError(textoError(err))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="tarjeta" onSubmit={enviar}>
      <h3>{editando ? `Actualizar trabajador ${inicial.codigo}` : 'Nuevo trabajador'}</h3>

      <h4 className="form-seccion">Datos personales</h4>
      <div className="form-grid">
        <Campo etiqueta="Código">{texto('codigo', { required: true, maxLength: 20 })}</Campo>
        <Campo etiqueta="Nombre y apellidos">{texto('nombre', { required: true })}</Campo>
        <Campo etiqueta="Carnet de identidad (11 dígitos)">
          {texto('carnet_identidad', { required: true, maxLength: 11, inputMode: 'numeric' })}
        </Campo>
        <Campo etiqueta="Nivel escolar">
          <select value={f.nivel_escolar} onChange={(e) => poner('nivel_escolar', e.target.value)}>
            {Object.entries(NIVELES).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </Campo>
        <Campo etiqueta="Dirección particular" completo>{texto('direccion', { required: true })}</Campo>
      </div>

      <h4 className="form-seccion">Puesto</h4>
      <div className="form-grid">
        <Campo etiqueta="Cargo">
          <select value={f.cargo} onChange={(e) => poner('cargo', e.target.value)}>
            {Object.entries(CARGOS).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </Campo>
        <Campo etiqueta="Categoría">
          <select value={f.categoria} onChange={(e) => poner('categoria', e.target.value)}>
            {letrasCargo.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </Campo>
        <Campo etiqueta="Departamento">{texto('departamento', { required: true })}</Campo>
        <Campo etiqueta="No. de plaza">{texto('numero_plaza', { required: true, maxLength: 20 })}</Campo>
        <Campo etiqueta="Centro principal">{texto('centro_principal', { required: true, maxLength: 30 })}</Campo>
        <Campo etiqueta="Centro asociado (opcional)">{texto('centro_asociado', { maxLength: 30 })}</Campo>
        <Campo etiqueta="Salario">
          <input type="number" step="0.01" min="0" value={f.salario} required
            onChange={(e) => poner('salario', e.target.value)} />
        </Campo>
      </div>

      <h4 className="form-seccion">Licencia de conducción</h4>
      <div className="form-grid">
        <Campo etiqueta="¿Tiene licencia de conducción?">
          <select value={f.licencia_conduccion ? 'si' : 'no'}
            onChange={(e) => poner('licencia_conduccion', e.target.value === 'si')}>
            <option value="no">No</option>
            <option value="si">Sí</option>
          </select>
        </Campo>
        {f.licencia_conduccion && (
          <>
            <Campo etiqueta="No. de licencia">{texto('numero_licencia', { required: true, maxLength: 30 })}</Campo>
            <Campo etiqueta="Categoría de la licencia">
              <select value={f.categoria_licencia} required
                onChange={(e) => poner('categoria_licencia', e.target.value)}>
                <option value="">-- Seleccione --</option>
                {LETRAS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </Campo>
          </>
        )}
      </div>

      <h4 className="form-seccion">Contacto (opcional)</h4>
      <div className="form-grid">
        <Campo etiqueta="Móvil">{texto('movil', { maxLength: 20, inputMode: 'tel' })}</Campo>
        <Campo etiqueta="Teléfono particular">{texto('telefono_particular', { maxLength: 20, inputMode: 'tel' })}</Campo>
        <Campo etiqueta="Teléfono de oficina">{texto('telefono_oficina', { maxLength: 20, inputMode: 'tel' })}</Campo>
      </div>

      {error && <div className="error">{error}</div>}
      <div className="fila-botones">
        <button className="btn btn-verde" disabled={enviando}>
          {enviando ? 'Guardando...' : editando ? 'Actualizar' : 'Guardar trabajador'}
        </button>
        <button type="button" className="btn btn-gris" onClick={onCancelar}>Cancelar</button>
      </div>
    </form>
  )
}
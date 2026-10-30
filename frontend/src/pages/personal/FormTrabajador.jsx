import { useEffect, useState } from 'react'
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

function Campo({ etiqueta, completo, ayuda, children }) {
  return (
    <div className={completo ? 'campo-completo' : ''}>
      <label style={{ marginTop: 0 }}>{etiqueta}</label>
      {children}
      {ayuda && <small className="pista">{ayuda}</small>}
    </div>
  )
}

const rotulo = (c) => (c.nombre ? `${c.codigo} - ${c.nombre}` : c.codigo)

export default function FormTrabajador({ inicial, onGuardado, onCancelar }) {
  const editando = Boolean(inicial?.id)
  const [f, setF] = useState({ ...VACIO, ...inicial })
  const [deptos, setDeptos] = useState([])
  const [centros, setCentros] = useState([])
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    Promise.all([api.get('departamentos/'), api.get('centros-telefonicos/')])
      .then(([d, c]) => {
        setDeptos(d.data)
        setCentros(c.data)
      })
      .catch((e) => setError(textoError(e)))
  }, [])

  const principales = centros.filter((c) => c.tipo === 'PRINCIPAL')
  const asociados = centros.filter((c) => c.tipo === 'ASOCIADO')

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
        <Campo
          etiqueta="Departamento"
          ayuda={deptos.length === 0 ? 'No hay departamentos: créelos en el admin (Catálogos).' : ''}
        >
          <select value={f.departamento} required onChange={(e) => poner('departamento', e.target.value)}>
            <option value="">-- Seleccione --</option>
            {deptos.map((d) => (
              <option key={d.id} value={d.id}>{d.acronimo ? `${d.acronimo} - ${d.nombre}` : d.nombre}</option>
            ))}
          </select>
        </Campo>
        <Campo etiqueta="No. de plaza">{texto('numero_plaza', { required: true, maxLength: 20 })}</Campo>
        <Campo
          etiqueta="Centro principal"
          ayuda={principales.length === 0 ? 'No hay centros principales: créelos en el admin.' : ''}
        >
          <select value={f.centro_principal} required onChange={(e) => poner('centro_principal', e.target.value)}>
            <option value="">-- Seleccione --</option>
            {principales.map((c) => <option key={c.id} value={c.id}>{rotulo(c)}</option>)}
          </select>
        </Campo>
        <Campo etiqueta="Centro asociado (opcional)">
          <select value={f.centro_asociado || ''} onChange={(e) => poner('centro_asociado', e.target.value)}>
            <option value="">-- Ninguno --</option>
            {asociados.map((c) => <option key={c.id} value={c.id}>{rotulo(c)}</option>)}
          </select>
        </Campo>
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
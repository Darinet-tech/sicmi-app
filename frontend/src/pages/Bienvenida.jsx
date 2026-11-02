import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import api from '../api'
import { useAuth } from '../AuthContext'
import { PASOS, ROLES } from '../bienvenidaContenido'

export default function Bienvenida() {
  const { usuario, marcarBienvenida } = useAuth()
  const navigate = useNavigate()
  const [afectaciones, setAfectaciones] = useState([])
  const [guardando, setGuardando] = useState(false)

  const primera = !usuario.bienvenida_vista
  const rol = ROLES[usuario.rol]

  useEffect(() => {
    api.get('grupos-genericos/').then((r) => setAfectaciones(r.data)).catch(() => {})
  }, [])

  async function comenzar() {
    setGuardando(true)
    await marcarBienvenida()
    navigate('/', { replace: true })
  }

  return (
    <>
      <section className="hero">
        <h2>Bienvenido a SiCMI, {usuario.nombre.split(' ')[0]}</h2>
        <p>
          SiCMI controla el mantenimiento a inmuebles por medios propios: desde que un directivo reporta una
          avería hasta que se cierra la orden de trabajo, con el control de los materiales, el personal, el
          transporte y el presupuesto, según el procedimiento PE-SG-020/18.
        </p>
        <div className="chips">
          <span className="chip">{usuario.rol_display}</span>
          <span className="chip">{usuario.uo_nombre || 'Nivel central'}</span>
        </div>
      </section>

      {primera && (
        <div className="aviso">
          Esta guía aparece solo en su primera visita. Podrá volver a consultarla cuando quiera con el botón
          <strong> ? </strong> de la barra superior.
        </div>
      )}

      <h3 className="seccion-titulo">Cómo funciona</h3>
      <section className="pasos">
        {PASOS.map((p) => {
          const mio = p.roles.includes(usuario.rol)
          return (
            <div key={p.n} className={`paso ${mio ? 'mio' : ''}`}>
              <div className="paso-num">{p.n}</div>
              <span className="quien-paso">{p.quien}</span>
              <h4>{p.titulo}</h4>
              <p>{p.texto}</p>
              {mio && <span className="paso-etq">Su participación</span>}
            </div>
          )
        })}
      </section>

      {rol && (
        <>
          <h3 className="seccion-titulo">Su papel: {rol.titulo}</h3>
          <div className="tarjeta">
            <p style={{ marginTop: 0 }}><strong>{rol.resumen}</strong></p>
            <ul className="rol-tareas">
              {rol.tareas.map((t) => <li key={t}>{t}</li>)}
            </ul>
            <h4 className="form-seccion">Empiece por aquí</h4>
            <div className="fila-botones" style={{ marginTop: 0 }}>
              {rol.acciones.map((a) => (
                <Link key={a.ruta} to={a.ruta} className={`btn ${a.principal ? 'btn-verde' : 'btn-gris'}`}>
                  {a.texto}
                </Link>
              ))}
            </div>
          </div>
        </>
      )}

      {afectaciones.length > 0 && (
        <>
          <h3 className="seccion-titulo">Afectaciones que puede seleccionar</h3>
          <div className="tarjeta">
            <p style={{ marginTop: 0 }}>
              Al crear una solicitud elegirá la afectación de esta lista y después la describirá con más detalle.
              Si lo que ocurre no aparece, elija <strong>«Otra afectación (no está en la lista)»</strong> y escriba cuál es.
            </p>
            <div className="afectaciones">
              {afectaciones.map((a) => (
                <span key={a.id} className="afect"><b>{a.numero}</b>{a.nombre}</span>
              ))}
              <span className="afect afect-otra">Otra afectación: escríbala usted</span>
            </div>
          </div>
        </>
      )}

      <div className="fila-botones">
        {primera ? (
          <button className="btn btn-verde" onClick={comenzar} disabled={guardando}>
            {guardando ? 'Guardando...' : <>Entendido, comenzar <ArrowRight size={16} style={{ verticalAlign: '-3px' }} /></>}
          </button>
        ) : (
          <Link className="btn btn-verde" to="/">Volver al inicio</Link>
        )}
      </div>
    </>
  )
}
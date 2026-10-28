import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Lock, Clock } from 'lucide-react'
import api from '../api'
import { useAuth } from '../AuthContext'
import { MODULOS, tieneAcceso } from '../modulos'

function saludo() {
  const h = new Date().getHours()
  return h < 12 ? 'Buenos días' : h < 19 ? 'Buenas tardes' : 'Buenas noches'
}

function Tarjeta({ modulo, rol }) {
  const Icono = modulo.icono
  const acceso = tieneAcceso(modulo, rol)

  const contenido = (
    <>
      <div className="modulo-icono">
        <Icono size={26} />
      </div>
      <h3>{modulo.titulo}</h3>
      <p>{modulo.descripcion}</p>
      <div className="modulo-pie">
        {!acceso ? (
          <><Lock size={15} /> Sin acceso para su rol</>
        ) : !modulo.disponible ? (
          <><Clock size={15} /> Próximamente · {modulo.fase}</>
        ) : (
          <>Abrir módulo <ArrowRight size={15} /></>
        )}
      </div>
    </>
  )

  if (acceso && modulo.disponible) {
    return <Link to={modulo.ruta} className="modulo activo">{contenido}</Link>
  }
  return <div className={`modulo ${acceso ? 'proximo' : 'bloqueado'}`}>{contenido}</div>
}

export default function Inicio() {
  const { usuario } = useAuth()
  const [solicitudes, setSolicitudes] = useState([])

  useEffect(() => {
    api.get('solicitudes/').then((r) => setSolicitudes(r.data)).catch(() => {})
  }, [])

  const enTramite = solicitudes.filter((s) => !['CERRADA', 'CANCELADA'].includes(s.estado))
  const urgentes = enTramite.filter((s) => s.es_urgente)

  return (
    <>
      <section className="hero">
        <h2>{saludo()}, {usuario.nombre.split(' ')[0]}</h2>
        <p>Bienvenido al Sistema de Control del Mantenimiento a Inmuebles.</p>
        <div className="chips">
          <span className="chip">{usuario.rol_display}</span>
          <span className="chip">{usuario.uo_nombre || 'Nivel central'}</span>
        </div>
      </section>

      <section className="stats">
        <div className="stat"><b>{solicitudes.length}</b><span>Solicitudes visibles</span></div>
        <div className="stat"><b>{enTramite.length}</b><span>En trámite</span></div>
        <div className={`stat ${urgentes.length ? 'alerta' : ''}`}>
          <b>{urgentes.length}</b><span>Urgentes en trámite</span>
        </div>
      </section>

      <h3 className="seccion-titulo">Módulos</h3>
      <section className="modulos">
        {MODULOS.map((m) => (
          <Tarjeta key={m.id} modulo={m} rol={usuario.rol} />
        ))}
      </section>
    </>
  )
}
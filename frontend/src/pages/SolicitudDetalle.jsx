import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { API_URL, textoError } from '../api'
import { useAuth } from '../AuthContext'
import { Etiqueta } from './Solicitudes'
import GenerarOrden from './GenerarOrden'

// Texto del botón según el estado al que llevaría la acción
const BOTONES = {
  EN_REVISION: { texto: 'Iniciar revisión', clase: 'btn' },
  DEVUELTA: { texto: 'Devolver al cliente', clase: 'btn btn-gris' },
  EN_INSPECCION: { texto: 'Aprobar y enviar a inspección', clase: 'btn btn-verde' },
  ENVIADA: { texto: 'Reenviar solicitud', clase: 'btn btn-verde' },
  EN_PROGRAMACION: { texto: 'Registrar inspección', clase: 'btn btn-verde' },
  ORDEN_GENERADA: { texto: 'Marcar orden generada', clase: 'btn btn-verde' },
  CERRADA: { texto: 'Cerrar solicitud', clase: 'btn btn-verde' },
  CANCELADA: { texto: 'Cancelar solicitud', clase: 'btn btn-peligro' },
}

export default function SolicitudDetalle() {
  const { id } = useParams()
  const { usuario } = useAuth()
  const [s, setS] = useState(null)
  const [error, setError] = useState('')

  // Acción en curso (para pedir comentario o urgencia antes de confirmar)
  const [accion, setAccion] = useState(null)
  const [comentario, setComentario] = useState('')
  const [urgente, setUrgente] = useState('') // '' = sin decidir, 'si' o 'no'
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    api
      .get(`solicitudes/${id}/`)
      .then((r) => setS(r.data))
      .catch((e) => setError(textoError(e)))
  }, [id])

  function elegir(estado) {
    setAccion(estado)
    setComentario('')
    setUrgente('')
    setError('')
  }

  async function confirmar() {
    setError('')
    if (accion === 'DEVUELTA' && !comentario.trim()) {
      return setError('Debe indicar el motivo de la devolución.')
    }
    if (accion === 'EN_PROGRAMACION' && !urgente) {
      return setError('Debe indicar si el trabajo es urgente o no.')
    }
    setEnviando(true)
    try {
      const cuerpo = { estado: accion, comentario }
      if (accion === 'EN_PROGRAMACION') cuerpo.es_urgente = urgente === 'si'
      const r = await api.post(`solicitudes/${id}/cambiar_estado/`, cuerpo)
      setS(r.data)
      setAccion(null)
    } catch (e) {
      setError(textoError(e))
    } finally {
      setEnviando(false)
    }
  }

  if (!s) return error ? <div className="error">{error}</div> : <p>Cargando...</p>

  const puedeEditar = usuario.rol === 'CLIENTE' && s.estado === 'DEVUELTA'
  const urlFoto = s.foto ? (s.foto.startsWith('http') ? s.foto : API_URL + s.foto) : null

  return (
    <>
      <div className="barra">
        <h2>
          Solicitud #{s.id} <Etiqueta estado={s.estado} />
          {s.es_urgente && <span className="etiqueta urgente">URGENTE</span>}
        </h2>
        <Link className="btn btn-gris" to="/solicitudes">← Volver</Link>
      </div>

      {s.estado === 'DEVUELTA' && (
        <div className="aviso">
          <strong>Motivo de la devolución:</strong> {s.motivo_devolucion}
        </div>
      )}

      <div className="tarjeta">
        <h3>Datos de la solicitud</h3>
        <dl className="datos">
          <dt>Inmueble</dt><dd>{s.inmueble_nombre}</dd>
          <dt>Área solicitante</dt><dd>{s.area_nombre}</dd>
          <dt>Local</dt><dd>{s.local_nombre}</dd>
          <dt>Afectación</dt><dd>{s.afectacion_nombre || s.otra_afectacion}</dd>
          <dt>Solicitante</dt><dd>{s.solicitante_nombre}</dd>
          <dt>Fecha</dt><dd>{new Date(s.creada).toLocaleString('es')}</dd>
          <dt>Descripción</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{s.descripcion}</dd>
        </dl>
        {urlFoto && (
          <p>
            <img className="foto" src={urlFoto} alt="Foto de la avería" />
          </p>
        )}
      </div>

      <GenerarOrden solicitud={s} />

      {(s.acciones_permitidas.length > 0 || puedeEditar) && (
        <div className="tarjeta">
          <h3>Acciones</h3>
          {!accion && (
            <div className="fila-botones" style={{ marginTop: 0 }}>
              {puedeEditar && (
                <Link className="btn" to={`/solicitudes/${s.id}/editar`}>Corregir datos</Link>
              )}
              {s.acciones_permitidas.map((estado) => (
                <button key={estado} className={BOTONES[estado].clase} onClick={() => elegir(estado)}>
                  {BOTONES[estado].texto}
                </button>
              ))}
            </div>
          )}

          {accion && (
            <>
              <strong>{BOTONES[accion].texto}</strong>

              {accion === 'EN_PROGRAMACION' && (
                <>
                  <label>Tras la inspección, ¿el trabajo es urgente?</label>
                  <select value={urgente} onChange={(e) => setUrgente(e.target.value)}>
                    <option value="">-- Seleccione --</option>
                    <option value="si">Sí: fuga, salidero o rotura que impide usar el inmueble</option>
                    <option value="no">No: se programa dentro del año</option>
                  </select>
                </>
              )}

              <label>
                Comentario {accion === 'DEVUELTA' ? '(obligatorio: motivo)' : '(opcional)'}
              </label>
              <textarea value={comentario} onChange={(e) => setComentario(e.target.value)} />

              {error && <div className="error">{error}</div>}
              <div className="fila-botones">
                <button className="btn btn-verde" onClick={confirmar} disabled={enviando}>
                  {enviando ? 'Guardando...' : 'Confirmar'}
                </button>
                <button className="btn btn-gris" onClick={() => setAccion(null)}>Volver</button>
              </div>
            </>
          )}
          {!accion && error && <div className="error">{error}</div>}
        </div>
      )}

      <div className="tarjeta">
        <h3>Historial</h3>
        <ul className="historial">
          {s.historial.map((h, i) => (
            <li key={i}>
              <strong>{h.estado_anterior ? `${h.estado_anterior} → ` : ''}{h.estado_nuevo}</strong>
              <br />
              <small>{h.usuario} · {new Date(h.fecha).toLocaleString('es')}</small>
              {h.comentario && <div>{h.comentario}</div>}
            </li>
          ))}
        </ul>
      </div>
    </>
  )
}
import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { textoError } from '../api'

export default function Login() {
  const { usuario, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (usuario) return <Navigate to="/solicitudes" replace />

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)
    try {
      await login(username, password)
      navigate('/solicitudes')
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Usuario o contraseña incorrectos.')
      } else {
        setError(textoError(err))
      }
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="login">
      <div className="tarjeta">
        <h2>SiCMI</h2>
        <p style={{ color: 'var(--gris)', marginTop: 0 }}>
          Sistema de Control del Mantenimiento a Inmuebles
        </p>
        <form onSubmit={enviar}>
          <label>Usuario</label>
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          <label>Contraseña</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          {error && <div className="error">{error}</div>}
          <div className="fila-botones">
            <button className="btn btn-verde" disabled={enviando}>
              {enviando ? 'Entrando...' : 'Entrar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
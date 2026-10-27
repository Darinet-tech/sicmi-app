import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [respuesta, setRespuesta] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios
      .get('http://127.0.0.1:8000/api/salud/')
      .then((res) => setRespuesta(res.data))
      .catch(() => setError('No se pudo conectar con el backend'))
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Sistema de Mantenimiento de Inmuebles</h1>
      {respuesta && <p style={{ color: 'green' }}>{respuesta.mensaje}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {!respuesta && !error && <p>Conectando...</p>}
    </div>
  )
}

export default App
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './AuthContext'
import Layout from './Layout'
import Login from './pages/Login'
import Solicitudes from './pages/Solicitudes'
import SolicitudForm from './pages/SolicitudForm'
import SolicitudDetalle from './pages/SolicitudDetalle'

// Protege las pantallas: sin sesión, redirige al login
function Privada({ children }) {
  const { usuario, cargando } = useAuth()
  if (cargando) return <p style={{ padding: '2rem' }}>Cargando...</p>
  return usuario ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <Privada>
            <Layout />
          </Privada>
        }
      >
        <Route index element={<Navigate to="/solicitudes" replace />} />
        <Route path="/solicitudes" element={<Solicitudes />} />
        <Route path="/solicitudes/nueva" element={<SolicitudForm />} />
        <Route path="/solicitudes/:id" element={<SolicitudDetalle />} />
        <Route path="/solicitudes/:id/editar" element={<SolicitudForm />} />
      </Route>
    </Routes>
  )
}
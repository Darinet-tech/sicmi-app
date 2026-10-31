import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './AuthContext'
import Layout from './Layout'
import Login from './pages/Login'
import Solicitudes from './pages/Solicitudes'
import SolicitudForm from './pages/SolicitudForm'
import SolicitudDetalle from './pages/SolicitudDetalle'
import Inicio from './pages/Inicio'
import PersonalLayout from './pages/personal/PersonalLayout'
import PaseLista from './pages/personal/PaseLista'
import Trabajadores from './pages/personal/Trabajadores'
import Brigadas from './pages/personal/Brigadas'
import TransporteLayout from './pages/transporte/TransporteLayout'
import ParteDiario from './pages/transporte/ParteDiario'
import Vehiculos from './pages/transporte/Vehiculos'
import OrdenesLista from './pages/ordenes/OrdenesLista'
import OrdenDetalle from './pages/ordenes/OrdenDetalle'
import RecursosLayout from './pages/recursos/RecursosLayout'
import ListaRecursos from './pages/recursos/ListaRecursos'
import NuevaSolicitudRecursos from './pages/recursos/NuevaSolicitudRecursos'
import DetalleRecurso from './pages/recursos/DetalleRecurso'
import Existencias from './pages/recursos/Existencias'
import Presupuesto from './pages/recursos/Presupuesto'

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
        <Route index element={<Inicio />} />
        <Route path="/solicitudes" element={<Solicitudes />} />
        <Route path="/solicitudes/nueva" element={<SolicitudForm />} />
        <Route path="/solicitudes/:id" element={<SolicitudDetalle />} />
        <Route path="/solicitudes/:id/editar" element={<SolicitudForm />} />
        <Route path="/personal" element={<PersonalLayout />}>
          <Route index element={<Navigate to="pase-lista" replace />} />
          <Route path="pase-lista" element={<PaseLista />} />
          <Route path="trabajadores" element={<Trabajadores />} />
          <Route path="brigadas" element={<Brigadas />} />
        </Route>
        <Route path="/transporte" element={<TransporteLayout />}>
          <Route index element={<Navigate to="parte-diario" replace />} />
          <Route path="parte-diario" element={<ParteDiario />} />
          <Route path="vehiculos" element={<Vehiculos />} />
        </Route>
        <Route path="/ordenes" element={<OrdenesLista />} />
        <Route path="/ordenes/:id" element={<OrdenDetalle />} />
        <Route path="/recursos" element={<RecursosLayout />}>
          <Route index element={<Navigate to="solicitudes" replace />} />
          <Route path="solicitudes" element={<ListaRecursos />} />
          <Route path="solicitudes/nueva" element={<NuevaSolicitudRecursos />} />
          <Route path="solicitudes/:id" element={<DetalleRecurso />} />
          <Route path="existencias" element={<Existencias />} />
          <Route path="presupuesto" element={<Presupuesto />} />
        </Route>

      </Route>
    </Routes>
  )
}
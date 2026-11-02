import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import Layout from './Layout'
import Login from './pages/Login'
import Inicio from './pages/Inicio'
import Bienvenida from './pages/Bienvenida'
import Solicitudes from './pages/Solicitudes'
import SolicitudForm from './pages/SolicitudForm'
import SolicitudDetalle from './pages/SolicitudDetalle'
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
import SobrantesCustodia from './pages/recursos/SobrantesCustodia'
import PlanLista from './pages/plan/PlanLista'
import PlanDetalle from './pages/plan/PlanDetalle'
import DocumentacionTecnica from './pages/plan/DocumentacionTecnica'
import GenerarOrdenPlan from './pages/plan/GenerarOrdenPlan'

// Protege las pantallas: sin sesión, al login; en la primera visita, a la bienvenida
function Privada({ children }) {
  const { usuario, cargando } = useAuth()
  const { pathname } = useLocation()
  if (cargando) return <p style={{ padding: '2rem' }}>Cargando...</p>
  if (!usuario) return <Navigate to="/login" replace />
  if (!usuario.bienvenida_vista && pathname !== '/bienvenida') {
    return <Navigate to="/bienvenida" replace />
  }
  return children
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
        <Route path="/bienvenida" element={<Bienvenida />} />

        <Route path="/solicitudes" element={<Solicitudes />} />
        <Route path="/solicitudes/nueva" element={<SolicitudForm />} />
        <Route path="/solicitudes/:id" element={<SolicitudDetalle />} />
        <Route path="/solicitudes/:id/editar" element={<SolicitudForm />} />

        <Route path="/ordenes" element={<OrdenesLista />} />
        <Route path="/ordenes/:id" element={<OrdenDetalle />} />

        <Route path="/plan" element={<PlanLista />} />
        <Route path="/plan/:id" element={<PlanDetalle />} />
        <Route path="/plan/acciones/:id/documentacion" element={<DocumentacionTecnica />} />
        <Route path="/plan/acciones/:id/generar" element={<GenerarOrdenPlan />} />

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

        <Route path="/recursos" element={<RecursosLayout />}>
          <Route index element={<Navigate to="solicitudes" replace />} />
          <Route path="solicitudes" element={<ListaRecursos />} />
          <Route path="solicitudes/nueva" element={<NuevaSolicitudRecursos />} />
          <Route path="solicitudes/:id" element={<DetalleRecurso />} />
          <Route path="existencias" element={<Existencias />} />
          <Route path="presupuesto" element={<Presupuesto />} />
          <Route path="sobrantes" element={<SobrantesCustodia />} />
        </Route>
      </Route>
    </Routes>
  )
}
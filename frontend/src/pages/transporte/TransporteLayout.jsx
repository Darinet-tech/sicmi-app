import { NavLink, Outlet } from 'react-router-dom'
import { ClipboardCheck, Car, Lock } from 'lucide-react'
import PaginaModulo from '../../PaginaModulo'
import { useAuth } from '../../AuthContext'
import { MODULOS, tieneAcceso } from '../../modulos'

const SECCIONES = [
  { a: 'parte-diario', texto: 'Parte diario', icono: ClipboardCheck },
  { a: 'vehiculos', texto: 'Vehículos', icono: Car },
]

export default function TransporteLayout() {
  const { usuario } = useAuth()
  const modulo = MODULOS.find((m) => m.id === 'transporte')

  if (!tieneAcceso(modulo, usuario.rol)) {
    return (
      <PaginaModulo icono={Lock} titulo="Transporte">
        <div className="aviso">Su rol no tiene acceso a este módulo.</div>
      </PaginaModulo>
    )
  }

  return (
    <PaginaModulo
      icono={modulo.icono}
      titulo="Transporte"
      descripcion="Disponibilidad diaria de los vehículos y causas de paralización."
    >
      <div className="modulo-layout">
        <nav className="menu-lateral">
          {SECCIONES.map(({ a, texto, icono: Icono }) => (
            <NavLink key={a} to={a} className={({ isActive }) => (isActive ? 'activo' : '')}>
              <Icono size={18} /> {texto}
            </NavLink>
          ))}
        </nav>
        <div className="modulo-contenido">
          <Outlet />
        </div>
      </div>
    </PaginaModulo>
  )
}
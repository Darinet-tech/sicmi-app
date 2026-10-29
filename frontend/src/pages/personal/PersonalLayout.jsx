import { NavLink, Outlet } from 'react-router-dom'
import { ClipboardCheck, Users, HardHat, Lock } from 'lucide-react'
import PaginaModulo from '../../PaginaModulo'
import { useAuth } from '../../AuthContext'
import { MODULOS, tieneAcceso } from '../../modulos'

const SECCIONES = [
  { a: 'pase-lista', texto: 'Pase de lista', icono: ClipboardCheck },
  { a: 'trabajadores', texto: 'Trabajadores', icono: Users },
  { a: 'brigadas', texto: 'Brigadas', icono: HardHat },
]

export default function PersonalLayout() {
  const { usuario } = useAuth()
  const modulo = MODULOS.find((m) => m.id === 'personal')

  if (!tieneAcceso(modulo, usuario.rol)) {
    return (
      <PaginaModulo icono={Lock} titulo="Personal y brigadas">
        <div className="aviso">Su rol no tiene acceso a este módulo.</div>
      </PaginaModulo>
    )
  }

  return (
    <PaginaModulo
      icono={modulo.icono}
      titulo="Personal y brigadas"
      descripcion="Estado diario de los trabajadores y composición de las brigadas."
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
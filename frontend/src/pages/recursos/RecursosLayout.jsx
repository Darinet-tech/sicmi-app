import { NavLink, Outlet } from 'react-router-dom'
import { ClipboardList, Package, BarChart3, Lock } from 'lucide-react'
import PaginaModulo from '../../PaginaModulo'
import { useAuth } from '../../AuthContext'
import { MODULOS, tieneAcceso } from '../../modulos'

const VE_PRESUPUESTO = ['ESPECIALISTA', 'JEFE_LOGISTICA', 'DIRECTOR_UO', 'CENTRAL']

export default function RecursosLayout() {
  const { usuario } = useAuth()
  const modulo = MODULOS.find((m) => m.id === 'recursos')

  if (!tieneAcceso(modulo, usuario.rol)) {
    return (
      <PaginaModulo icono={Lock} titulo="Recursos y materiales">
        <div className="aviso">Su rol no tiene acceso a este módulo.</div>
      </PaginaModulo>
    )
  }

  const secciones = [
    { a: 'solicitudes', texto: 'Solicitudes de recursos', icono: ClipboardList },
    { a: 'existencias', texto: 'Existencias', icono: Package },
    ...(VE_PRESUPUESTO.includes(usuario.rol)
      ? [{ a: 'presupuesto', texto: 'Presupuesto y sobregiros', icono: BarChart3 }]
      : []),
  ]

  return (
    <PaginaModulo
      icono={modulo.icono}
      titulo="Recursos y materiales"
      descripcion="Solicitudes de recursos, existencias del almacén, presupuesto y sobregiros."
    >
      <div className="modulo-layout">
        <nav className="menu-lateral">
          {secciones.map(({ a, texto, icono: Icono }) => (
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
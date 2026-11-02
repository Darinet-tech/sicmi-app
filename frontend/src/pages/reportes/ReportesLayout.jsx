import { NavLink, Outlet } from 'react-router-dom'
import { BarChart3, FileCheck2, Lock } from 'lucide-react'
import PaginaModulo from '../../PaginaModulo'
import { useAuth } from '../../AuthContext'
import { MODULOS, tieneAcceso } from '../../modulos'

const SECCIONES = [
  { a: 'resumen', texto: 'Resumen y gráficos', icono: BarChart3 },
  { a: 'certificaciones', texto: 'Certificación mensual', icono: FileCheck2 },
]

export default function ReportesLayout() {
  const { usuario } = useAuth()
  const modulo = MODULOS.find((m) => m.id === 'reportes')

  if (!modulo || !tieneAcceso(modulo, usuario.rol)) {
    return (
      <PaginaModulo icono={Lock} titulo="Reportes e indicadores">
        <div className="aviso">Su rol no tiene acceso a este módulo.</div>
      </PaginaModulo>
    )
  }

  return (
    <PaginaModulo
      icono={modulo.icono}
      titulo="Reportes e indicadores"
      descripcion="Indicadores de medición, gráficos y certificación mensual del mantenimiento."
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
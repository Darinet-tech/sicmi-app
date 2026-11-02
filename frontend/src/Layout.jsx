import { Link, Outlet, useLocation } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useAuth } from './AuthContext'
import ErrorBoundary from './ErrorBoundary'
import LogoEtecsa from './LogoEtecsa'
import LogoSiCMI from './LogoSiCMI'

export default function Layout() {
  const { usuario, logout } = useAuth()
  const { pathname } = useLocation()
  const iniciales = usuario.nombre
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  return (
    <>
      <header className="topbar">
        <div className="topbar-izq">
          <LogoEtecsa size={48} />
          <span className="marca-sep" />
          <Link to="/" className="marca">
            <LogoSiCMI size={38} />
            <div>
              <b>SiCMI</b>
              <small>Control del Mantenimiento a Inmuebles</small>
            </div>
          </Link>
        </div>
        <div className="topbar-der">
          <div className="quien">
            <div>{usuario.nombre}</div>
            <small>{usuario.rol_display}</small>
          </div>
          <div className="avatar">{iniciales}</div>
          <Link to="/bienvenida" className="btn-icono" title="Guía de bienvenida" aria-label="Guía de bienvenida">
            ?
          </Link>
          <button className="btn-icono" onClick={logout} title="Cerrar sesión">
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <main className="contenedor">
        <ErrorBoundary key={pathname}>
          <Outlet />
        </ErrorBoundary>
      </main>
      <footer className="pie-app">
        SiCMI · Sistema de Control del Mantenimiento a Inmuebles · ETECSA ·{' '}
        <Link to="/bienvenida">Guía de bienvenida</Link>
      </footer>
    </>
  )
}
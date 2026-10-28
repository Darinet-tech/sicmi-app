import { Link, Outlet } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useAuth } from './AuthContext'

export default function Layout() {
  const { usuario, logout } = useAuth()
  const iniciales = usuario.nombre
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  return (
    <>
      <header className="topbar">
        <Link to="/" className="marca">
          <div className="marca-logo">Si</div>
          <div>
            <b>SiCMI</b>
            <small>Control del Mantenimiento a Inmuebles</small>
          </div>
        </Link>
        <div className="topbar-der">
          <div className="quien">
            <div>{usuario.nombre}</div>
            <small>{usuario.rol_display}</small>
          </div>
          <div className="avatar">{iniciales}</div>
          <button className="btn-icono" onClick={logout} title="Cerrar sesión">
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <main className="contenedor">
        <Outlet />
      </main>
    </>
  )
}
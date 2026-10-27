import { Link, Outlet } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function Layout() {
  const { usuario, logout } = useAuth()

  return (
    <>
      <header className="encabezado">
        <div>
          <Link to="/solicitudes" style={{ color: '#fff', textDecoration: 'none' }}>
            <h1>SiCMI</h1>
          </Link>
          <small>Sistema de Control del Mantenimiento a Inmuebles</small>
        </div>
        <div className="usuario">
          <div>{usuario.nombre}</div>
          <small>
            {usuario.rol_display} · {usuario.uo_nombre || 'Nivel central'}
          </small>
          <div>
            <button className="btn btn-gris" onClick={logout} style={{ marginTop: 4 }}>
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>
      <main className="contenedor">
        <Outlet />
      </main>
    </>
  )
}
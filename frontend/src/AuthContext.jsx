import { createContext, useContext, useEffect, useState } from 'react'
import api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(true)

  // Al abrir la app: si hay token guardado, pedimos quién es
  useEffect(() => {
    if (!localStorage.getItem('token')) {
      setCargando(false)
      return
    }
    api
      .get('yo/')
      .then((r) => setUsuario(r.data))
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setCargando(false))
  }, [])

  async function login(username, password) {
    const { data } = await api.post('token/', { username, password })
    localStorage.setItem('token', data.access)
    try {
    const yo = await api.get('yo/')
      setUsuario(yo.data)
    } catch (e) {
      localStorage.removeItem('token')
      throw e
    }
  }

  function logout() {
    localStorage.removeItem('token')
    setUsuario(null)
  }

  return (
    <AuthContext.Provider value={{ usuario, cargando, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
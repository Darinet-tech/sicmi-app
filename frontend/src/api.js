import axios from 'axios'

export const API_URL = 'http://127.0.0.1:8000'

const api = axios.create({ baseURL: `${API_URL}/api/` })

// Antes de cada petición, agrega el token guardado
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Si el servidor responde 401 (sesión vencida), volvemos al login
api.interceptors.response.use(
  (respuesta) => respuesta,
  (error) => {
    const esLogin = error.config?.url?.includes('token')
    if (error.response?.status === 401 && !esLogin) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Convierte los errores de DRF en un texto legible
export function textoError(error) {
  const datos = error.response?.data
  if (!datos) return 'No se pudo conectar con el servidor.'
  if (typeof datos === 'string') return datos
  if (datos.detalle) return datos.detalle
  if (datos.detail) return datos.detail
  return Object.entries(datos)
    .map(([campo, msg]) => `${campo}: ${Array.isArray(msg) ? msg.join(' ') : msg}`)
    .join(' | ')
}

export default api
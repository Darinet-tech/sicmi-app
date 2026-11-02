import { useState } from 'react'
import { Printer, FileText, Download } from 'lucide-react'
import api, { textoError } from './api'

// Cuando la respuesta es un archivo, el error llega como Blob: hay que leerlo
async function mensaje(e) {
  const d = e.response?.data
  if (d instanceof Blob) {
    try {
      const j = JSON.parse(await d.text())
      return j.detalle || j.detail || 'No se pudo generar el documento.'
    } catch {
      return 'No se pudo generar el documento.'
    }
  }
  return textoError(e)
}

const BOTONES = [
  ['imprimir', Printer, 'Imprimir'],
  ['pdf', FileText, 'PDF'],
  ['xlsx', Download, 'Excel'],
]

export default function ExportarAnexo({ titulo, ruta, params = {}, nombre, compacto = false }) {
  const [ocupado, setOcupado] = useState('')
  const [error, setError] = useState('')

  async function accion(formato) {
    setError('')
    setOcupado(formato)
    // La pestaña se abre ya, con el clic, para que el navegador no la bloquee
    const ventana = formato === 'imprimir' ? window.open('', '_blank') : null
    try {
      const r = await api.get(ruta, {
        params: { ...params, formato: formato === 'imprimir' ? 'pdf' : formato },
        responseType: 'blob',
      })
      const url = URL.createObjectURL(r.data)
      if (formato === 'imprimir') {
        if (ventana) ventana.location.href = url
        else setError('El navegador bloqueó la ventana. Permita las ventanas emergentes o use PDF.')
      } else {
        const a = document.createElement('a')
        a.href = url
        a.download = `${nombre}.${formato}`
        document.body.appendChild(a)
        a.click()
        a.remove()
        setTimeout(() => URL.revokeObjectURL(url), 10000)
      }
    } catch (e) {
      if (ventana) ventana.close()
      setError(await mensaje(e))
    } finally {
      setOcupado('')
    }
  }

  return (
    <div className={`exportar ${compacto ? 'compacto' : ''}`}>
      {!compacto && <b>{titulo}</b>}
      {BOTONES.map(([formato, Icono, texto]) => (
        <button
          key={formato}
          type="button"
          className="btn btn-gris"
          disabled={Boolean(ocupado)}
          title={`${texto} · ${titulo}`}
          onClick={() => accion(formato)}
        >
          <Icono size={15} />
          {!compacto && ` ${texto}`}
        </button>
      ))}
      {error && <span className="error" style={{ margin: 0, flexBasis: '100%' }}>{error}</span>}
    </div>
  )
}
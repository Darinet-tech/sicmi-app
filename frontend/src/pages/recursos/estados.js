export const ESTADOS_RECURSO = {
  SOLICITADA: 'Solicitada',
  PENDIENTE_SOBREGIRO: 'Pendiente de sobregiro',
  VERIFICADA: 'Verificada · por autorizar',
  AUTORIZADA: 'Autorizada · por despachar',
  DESPACHADA: 'Despachada',
  RECHAZADA: 'Rechazada',
  CANCELADA: 'Cancelada',
}

// Formato de dinero: 1 234,50
export const dinero = (n) =>
  Number(n || 0).toLocaleString('es', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const ESTADOS_ORDEN = {
  EN_PROCESO: 'En proceso (sin generar)',
  REGISTRADA: 'Registrada',
  EN_EJECUCION: 'En ejecución',
  ENTREGADA: 'Entregada al cliente',
  CONFORME: 'Conforme · en firmas',
  CERRADA: 'Cerrada',
  CANCELADA: 'Cancelada',
}

// Orden en que se firma una orden
export const CADENA_FIRMAS = [
  ['CLIENTE', 'Cliente'],
  ['JEFE_BRIGADA', 'Jefe de Brigada'],
  ['JEFE_GRUPO', 'Jefe de Grupo de Servicios'],
  ['ESPECIALISTA', 'Especialista en Obras de Ingeniería'],
]
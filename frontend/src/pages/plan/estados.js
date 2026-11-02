export const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
  'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
export const MESES_ABR = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

export const ESTADOS_PLAN = {
  BORRADOR: 'En elaboración',
  EN_FIRMAS: 'En revisión y firmas',
  APROBADO: 'Aprobado',
}

export const VIAS = {
  PROPIOS: 'Medios propios',
  TERCEROS: 'Con terceros',
  INVERSION: 'Tarea de inversión',
}

// Orden de prioridad del procedimiento (numeral 7.2.1)
export const PRIORIDADES = {
  1: 'Vulnerabilidades y seguridad del inmueble',
  2: 'Filtraciones, fugas y humedad',
  3: 'Cambio climático y eficiencia energética',
  4: 'Mejora de la imagen',
}

export const CADENA_PLAN = [
  ['ESPECIALISTA', 'Confeccionado · Especialista'],
  ['JEFE_GRUPO', 'Revisado · Jefe de Grupo de Servicios'],
  ['JEFE_LOGISTICA', 'Revisado · Jefe de Dpto. de Logística y Servicios'],
  ['DIRECTOR_UO', 'Aprobado · Director de la UO'],
]

// Ciclos de referencia del procedimiento, por número de grupo genérico
const PINTURA =
  'Referencia del procedimiento: repintar los paramentos exteriores e interiores y el techo cada 5 años; ' +
  'las fachadas con pintura a base de agua cada 3 años. Los ciclos pueden acortarse según la ubicación y función del inmueble.'
const RETOQUE = 'Referencia del procedimiento: la pintura de los elementos metálicos y de carpintería debe retocarse cada 3 años.'
export const CICLOS = { 15: PINTURA, 4: RETOQUE, 14: RETOQUE, 18: RETOQUE }

export const dineroMcup = (n) =>
  Number(n || 0).toLocaleString('es', { minimumFractionDigits: 2, maximumFractionDigits: 3 })
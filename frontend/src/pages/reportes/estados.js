export const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
  'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

export const ESTADOS_CERT = {
  BORRADOR: 'En elaboración',
  EN_FIRMAS: 'En revisión y firmas',
  APROBADA: 'Aprobada',
}

export const CADENA_CERT = [
  ['ESPECIALISTA', 'Elaborado · Especialista en Obras de Ingenierías'],
  ['JEFE_GRUPO', 'Revisado · Jefe de Grupo de Servicios'],
  ['JEFE_LOGISTICA', 'Aprobado · Jefe de Dpto. de Logística y Servicios'],
]

export const porc = (v) => (v === null || v === undefined ? '—' : `${v} %`)
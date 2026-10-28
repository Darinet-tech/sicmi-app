import { ClipboardList, FileCheck2, Package, CalendarRange, BarChart3, Building2 } from 'lucide-react'

// roles: 'todos' o una lista de roles con acceso
// disponible: false = módulo aún no construido
export const MODULOS = [
  {
    id: 'solicitudes',
    titulo: 'Solicitudes de servicio',
    descripcion: 'Registre, revise e inspeccione solicitudes de mantenimiento correctivo.',
    icono: ClipboardList,
    ruta: '/solicitudes',
    roles: 'todos',
    disponible: true,
  },
  {
    id: 'ordenes',
    titulo: 'Órdenes de trabajo',
    descripcion: 'Seguimiento de la ejecución, entrega y firma de cada orden.',
    icono: FileCheck2,
    ruta: '/ordenes',
    roles: 'todos',
    disponible: false,
    fase: 'Fase 4',
  },
  {
    id: 'recursos',
    titulo: 'Recursos y materiales',
    descripcion: 'Solicitudes de recursos, existencias del almacén y sobregiros.',
    icono: Package,
    ruta: '/recursos',
    roles: ['ESPECIALISTA', 'JEFE_BRIGADA', 'BALANCISTA', 'JEFE_LOGISTICA', 'CENTRAL'],
    disponible: false,
    fase: 'Fase 4',
  },
  {
    id: 'plan',
    titulo: 'Plan anual preventivo',
    descripcion: 'Planificación anual por inmueble, cronograma y aprobación.',
    icono: CalendarRange,
    ruta: '/plan',
    roles: ['ESPECIALISTA', 'JEFE_GRUPO', 'JEFE_LOGISTICA', 'DIRECTOR_UO', 'CENTRAL'],
    disponible: false,
    fase: 'Fase 5',
  },
  {
    id: 'reportes',
    titulo: 'Reportes e indicadores',
    descripcion: 'Certificación mensual, cumplimiento del plan y gastos.',
    icono: BarChart3,
    ruta: '/reportes',
    roles: ['ESPECIALISTA', 'JEFE_GRUPO', 'JEFE_LOGISTICA', 'DIRECTOR_UO', 'CENTRAL'],
    disponible: false,
    fase: 'Fase 6',
  },
  {
    id: 'inmuebles',
    titulo: 'Inmuebles y catálogos',
    descripcion: 'Consulta del inventario de inmuebles y centros de costo.',
    icono: Building2,
    ruta: '/inmuebles',
    roles: ['ESPECIALISTA', 'JEFE_LOGISTICA', 'CENTRAL'],
    disponible: false,
    fase: 'Fase 7',
  },
]

export function tieneAcceso(modulo, rol) {
  return modulo.roles === 'todos' || modulo.roles.includes(rol)
}
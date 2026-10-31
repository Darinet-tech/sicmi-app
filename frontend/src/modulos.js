import {
  ClipboardList, FileCheck2, Package, CalendarRange,
  BarChart3, Building2, Users, Truck,
} from 'lucide-react'

// roles: 'todos' o una lista de roles con acceso
// disponible: false = módulo aún no construido
const GESTION = ['ESPECIALISTA', 'JEFE_BRIGADA', 'JEFE_GRUPO', 'JEFE_LOGISTICA', 'DIRECTOR_UO', 'CENTRAL']

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
    disponible: true,
    fase: 'Fase 4',
  },
  {
    id: 'personal',
    titulo: 'Personal y brigadas',
    descripcion: 'Estado diario de los trabajadores y composición de las brigadas.',
    icono: Users,
    ruta: '/personal',
    roles: GESTION,
    disponible: true,
  },
  {
    id: 'transporte',
    titulo: 'Transporte',
    descripcion: 'Disponibilidad diaria de los vehículos y causas de paralización.',
    icono: Truck,
    ruta: '/transporte',
    roles: GESTION,
    disponible: true,
  },
  {
    id: 'recursos',
    titulo: 'Recursos y materiales',
    descripcion: 'Solicitudes de recursos, existencias del almacén y sobregiros.',
    icono: Package,
    ruta: '/recursos',
    roles: ['ESPECIALISTA', 'JEFE_BRIGADA', 'BALANCISTA', 'JEFE_LOGISTICA', 'DIRECTOR_UO', 'CENTRAL'],
    disponible: true,
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
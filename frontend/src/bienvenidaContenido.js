// Pasos del flujo. "roles" son los que participan en cada paso (se resaltan en la guía).
export const PASOS = [
  {
    n: 1, titulo: 'Solicitud', quien: 'Cliente',
    texto: 'El directivo del área reporta la avería: elige el inmueble, el área, el local y la afectación, y la describe con detalle. Puede adjuntar una foto.',
    roles: ['CLIENTE'],
  },
  {
    n: 2, titulo: 'Revisión', quien: 'Jefe de Logística y Servicios · Jefe de Grupo',
    texto: 'Comprueban que la solicitud esté completa. La aprueban para inspección o la devuelven al cliente con el motivo.',
    roles: ['JEFE_LOGISTICA', 'JEFE_GRUPO'],
  },
  {
    n: 3, titulo: 'Inspección', quien: 'Jefe de Brigada · Especialista',
    texto: 'Visitan el lugar, confirman la avería y deciden si el trabajo es urgente (fugas, salideros o roturas que impiden usar el inmueble).',
    roles: ['JEFE_BRIGADA', 'ESPECIALISTA'],
  },
  {
    n: 4, titulo: 'Preparación', quien: 'Especialista',
    texto: 'Crea la orden de trabajo En proceso, asigna brigada, participantes y vehículo, y solicita los recursos necesarios.',
    roles: ['ESPECIALISTA'],
  },
  {
    n: 5, titulo: 'Recursos', quien: 'Especialista · Jefe de Logística · Balancista',
    texto: 'Se verifica el financiamiento, se autoriza y se despachan los materiales con su número de vale de salida. Sin el vale no se puede generar la orden. Si el presupuesto no alcanza, el Director de la UO pide un sobregiro.',
    roles: ['ESPECIALISTA', 'JEFE_LOGISTICA', 'BALANCISTA', 'JEFE_BRIGADA', 'DIRECTOR_UO', 'CENTRAL'],
  },
  {
    n: 6, titulo: 'Ejecución', quien: 'Brigada de mantenimiento',
    texto: 'Al cumplirse los requisitos se genera la orden con su número oficial. La brigada ejecuta el trabajo y los materiales sobrantes se devuelven al almacén o quedan en custodia.',
    roles: ['JEFE_BRIGADA', 'ESPECIALISTA', 'BALANCISTA'],
  },
  {
    n: 7, titulo: 'Cierre', quien: 'Cliente · Jefe de Brigada · Jefe de Grupo · Especialista',
    texto: 'Se entrega el trabajo y el cliente da su conformidad. Después firman, en orden, el Jefe de Brigada, el Jefe de Grupo y el Especialista, que cierra la orden y la solicitud.',
    roles: ['CLIENTE', 'JEFE_BRIGADA', 'JEFE_GRUPO', 'ESPECIALISTA'],
  },
]

// Qué hace cada rol y desde dónde empezar
export const ROLES = {
  CLIENTE: {
    titulo: 'Cliente',
    resumen: 'Usted reporta las averías de su área y confirma que el trabajo quedó bien.',
    tareas: [
      'Crear solicitudes eligiendo inmueble, área, local y afectación, y describir el problema con detalle.',
      'Adjuntar una foto de la avería (opcional).',
      'Si le devuelven una solicitud, corregirla y reenviarla.',
      'Cuando se le entregue el trabajo, confirmar su conformidad. Si no está conforme, indicar el motivo y el trabajo se rectifica.',
      'Usted solo ve sus propias solicitudes y órdenes.',
    ],
    acciones: [
      { texto: 'Nueva solicitud', ruta: '/solicitudes/nueva', principal: true },
      { texto: 'Mis solicitudes', ruta: '/solicitudes' },
      { texto: 'Mis órdenes', ruta: '/ordenes' },
    ],
  },
  JEFE_LOGISTICA: {
    titulo: 'Jefe de Departamento o Director de Logística y Servicios',
    resumen: 'Usted vela por el cumplimiento del procedimiento y autoriza el uso de recursos.',
    tareas: [
      'Revisar que las solicitudes estén completas: aprobarlas para inspección o devolverlas con el motivo.',
      'Autorizar o rechazar las solicitudes de recursos verificadas por el Especialista.',
      'Consultar el personal, el transporte y las órdenes de su UO.',
      'Cancelar solicitudes cuando corresponda.',
    ],
    acciones: [
      { texto: 'Solicitudes', ruta: '/solicitudes', principal: true },
      { texto: 'Recursos y materiales', ruta: '/recursos' },
      { texto: 'Personal y brigadas', ruta: '/personal' },
    ],
  },
  JEFE_GRUPO: {
    titulo: 'Jefe de Grupo de Servicios',
    resumen: 'Usted supervisa el trabajo de la brigada y firma las órdenes.',
    tareas: [
      'Revisar las solicitudes: aprobarlas para inspección o devolverlas con el motivo.',
      'Supervisar la ejecución y firmar la orden después del Jefe de Brigada.',
      'Cancelar solicitudes u órdenes cuando corresponda, indicando el motivo.',
      'Consultar el personal y el transporte de su UO.',
    ],
    acciones: [
      { texto: 'Solicitudes', ruta: '/solicitudes', principal: true },
      { texto: 'Órdenes de trabajo', ruta: '/ordenes' },
      { texto: 'Personal y brigadas', ruta: '/personal' },
    ],
  },
  JEFE_BRIGADA: {
    titulo: 'Jefe de Brigada',
    resumen: 'Usted inspecciona, dirige la ejecución y entrega el trabajo.',
    tareas: [
      'Inspeccionar el lugar e indicar si el trabajo es urgente.',
      'Completar la orden: participantes, descripción de los trabajos e incidencias.',
      'Solicitar y despachar recursos con su vale, y registrar los sobrantes.',
      'Iniciar la ejecución, entregar el trabajo al cliente y firmar la orden tras su conformidad.',
    ],
    acciones: [
      { texto: 'Solicitudes', ruta: '/solicitudes', principal: true },
      { texto: 'Órdenes de trabajo', ruta: '/ordenes' },
      { texto: 'Recursos y materiales', ruta: '/recursos' },
    ],
  },
  ESPECIALISTA: {
    titulo: 'Especialista en Obras de Ingenierías',
    resumen: 'Usted coordina todo el proceso y es quien cierra cada orden.',
    tareas: [
      'Actualizar cada día el pase de lista y el parte de transporte, y mantener los trabajadores y las brigadas.',
      'Preparar las órdenes En proceso y generarlas cuando se cumplan todos los requisitos.',
      'Verificar el financiamiento de las solicitudes de recursos.',
      'Firmar al final y cerrar la orden, y exportar los anexos del procedimiento.',
    ],
    acciones: [
      { texto: 'Pase de lista', ruta: '/personal/pase-lista', principal: true },
      { texto: 'Solicitudes', ruta: '/solicitudes' },
      { texto: 'Órdenes de trabajo', ruta: '/ordenes' },
      { texto: 'Recursos y materiales', ruta: '/recursos' },
    ],
  },
  BALANCISTA: {
    titulo: 'Balancista Distribuidor',
    resumen: 'Usted controla la salida y el regreso de los materiales del almacén.',
    tareas: [
      'Registrar el despacho de los materiales autorizados con el número del vale de salida.',
      'Registrar las devoluciones de sobrantes al almacén.',
      'Consultar las existencias en libre utilización.',
    ],
    acciones: [
      { texto: 'Solicitudes de recursos', ruta: '/recursos/solicitudes', principal: true },
      { texto: 'Existencias', ruta: '/recursos/existencias' },
    ],
  },
  DIRECTOR_UO: {
    titulo: 'Director de la UO',
    resumen: 'Usted sigue el presupuesto de mantenimiento y pide sobregiros cuando no alcanza.',
    tareas: [
      'Consultar el presupuesto: asignado, gastado, comprometido y disponible.',
      'Solicitar un sobregiro, con su fundamentación, cuando el presupuesto no alcanza.',
      'Seguir las órdenes, el personal y el transporte de su UO.',
    ],
    acciones: [
      { texto: 'Presupuesto y sobregiros', ruta: '/recursos/presupuesto', principal: true },
      { texto: 'Órdenes de trabajo', ruta: '/ordenes' },
      { texto: 'Personal y brigadas', ruta: '/personal' },
    ],
  },
  CENTRAL: {
    titulo: 'Nivel central',
    resumen: 'Usted consulta todas las Unidades Organizativas y resuelve los sobregiros.',
    tareas: [
      'Consultar solicitudes, órdenes y recursos de todas las UO.',
      'Aprobar o rechazar los sobregiros solicitados por las UO.',
      'Seguir el presupuesto de cada UO.',
    ],
    acciones: [
      { texto: 'Presupuesto y sobregiros', ruta: '/recursos/presupuesto', principal: true },
      { texto: 'Órdenes de trabajo', ruta: '/ordenes' },
      { texto: 'Solicitudes', ruta: '/solicitudes' },
    ],
  },
}
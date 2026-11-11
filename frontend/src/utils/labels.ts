const permissionLabels: Record<string, string> = {
  'users:read': 'Consultar usuarios',
  'users:manage': 'Administrar usuarios y roles',
  'customers:manage': 'Administrar clientes',
  'workshops:manage': 'Administrar talleres',
  'vehicles:manage': 'Administrar vehículos',
  'workorders:read': 'Consultar órdenes de trabajo',
  'workorders:write': 'Gestionar órdenes de trabajo',
}

const roleLabels: Record<string, string> = {
  administrador: 'Administrador', recepcionista: 'Recepcionista', tecnico: 'Técnico', secretaria: 'Secretaria',
}

export const permissionLabel = (code: string) => permissionLabels[code] || 'Acceso especial del sistema'
export const roleLabel = (name: string) => roleLabels[name.toLowerCase()] || name

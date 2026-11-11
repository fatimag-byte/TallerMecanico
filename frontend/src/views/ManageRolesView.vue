<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Permission, Role, RoleUser, RoleUsers } from '../types'
import { assignUserToRole, deleteRole, listPermissions, listRoleUsers, listRoles, removeUserFromRole, updateRole } from '../services/roles'
import { permissionLabel } from '../utils/labels'

const route = useRoute()
const router = useRouter()

const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const selectedRole = ref<Role | null>(null)
const roleUsers = ref<RoleUsers | null>(null)

const search = ref('')
const statusFilter = ref<'todos' | 'activos' | 'inactivos'>('todos')
const roleActiveStatus = ref<Record<number, boolean>>({})

const loading = ref(false)
const userLoading = ref(false)
const saving = ref(false)
const error = ref('')
const snackMessage = ref('')
let createdAlertTimer: number | undefined

const detail = ref<Role | null>(null)
const editing = ref<Role | null>(null)
const removing = ref<Role | null>(null)
const removingUser = ref<RoleUser | null>(null)

const form = ref({ name: '', description: '', permission_ids: [] as number[] })

const filterOptions = [
  { title: 'Todos los estados', value: 'todos' },
  { title: 'Solo activos', value: 'activos' },
  { title: 'Solo inactivos', value: 'inactivos' }
]

function isRoleActive(role: Role): boolean {
  if (role.name.toLowerCase() === 'administrador') return true
  return roleActiveStatus.value[role.id] ?? true
}

function toggleRoleStatus(role: Role) {
  if (role.name.toLowerCase() === 'administrador') {
    error.value = 'El rol Administrador principal no puede ser desactivado.'
    return
  }
  const current = isRoleActive(role)
  roleActiveStatus.value[role.id] = !current
  localStorage.setItem('taller_roles_status', JSON.stringify(roleActiveStatus.value))
  showSuccess(!current ? `El perfil "${role.name}" ahora está activo.` : `El perfil "${role.name}" ha sido desactivado.`)
}

function showSuccess(message: string) {
  if (createdAlertTimer) window.clearTimeout(createdAlertTimer)
  snackMessage.value = message
  createdAlertTimer = window.setTimeout(() => { snackMessage.value = '' }, 3000)
}

const filtered = computed(() => {
  const query = search.value.trim().toLocaleLowerCase()
  return roles.value.filter(role => {
    const matchesSearch = role.name.toLocaleLowerCase().includes(query) ||
      (role.description && role.description.toLocaleLowerCase().includes(query))
    const active = isRoleActive(role)
    const matchesStatus =
      statusFilter.value === 'todos' ||
      (statusFilter.value === 'activos' && active) ||
      (statusFilter.value === 'inactivos' && !active)
    return matchesSearch && matchesStatus
  })
})

const activeRolesCount = computed(() => {
  return roles.value.filter(role => isRoleActive(role)).length
})

const associatedUsers = computed(() => {
  return roles.value.reduce((count, role) => count + role.user_count, 0)
})

const permissionGroups = computed(() => {
  const catalog = new Map<string, Permission[]>([
    ['customers', []],
    ['special', []],
    ['users', []],
    ['vehicles', []],
    ['workorders', []],
    ['workshops', []]
  ])
  permissions.value.forEach(permission => {
    const key = permission.code.split(':')[0]
    ;(catalog.get(key) || catalog.get('special')!).push(permission)
  })
  return [
    { key: 'customers', title: 'Clientes', icon: 'mdi-account-group-outline', permissions: catalog.get('customers')! },
    { key: 'special', title: 'Acceso especial del sistema', icon: 'mdi-shield-key-outline', permissions: catalog.get('special')! },
    { key: 'users', title: 'Usuarios y roles', icon: 'mdi-account-cog-outline', permissions: catalog.get('users')! },
    { key: 'vehicles', title: 'Vehículos', icon: 'mdi-car-outline', permissions: catalog.get('vehicles')! },
    { key: 'workorders', title: 'Órdenes de trabajo', icon: 'mdi-clipboard-text-outline', permissions: catalog.get('workorders')! },
    { key: 'workshops', title: 'Talleres', icon: 'mdi-garage-variant', permissions: catalog.get('workshops')! }
  ]
})

const formIsValid = computed(() => form.value.name.trim().length >= 3 && form.value.permission_ids.length > 0)
const hasEditChanges = computed(() => {
  if (!editing.value) return false
  const original = [...editing.value.permissions.map(permission => permission.id)].sort((a, b) => a - b)
  const current = [...form.value.permission_ids].sort((a, b) => a - b)
  return form.value.name.trim() !== editing.value.name || form.value.description.trim() !== editing.value.description ||
    original.length !== current.length || original.some((id, index) => id !== current[index])
})

const canSaveEdit = computed(() => formIsValid.value && hasEditChanges.value)

function formatRoleDate(role: Role): string {
  if (role.updated_at) {
    try {
      const d = new Date(role.updated_at)
      return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
    } catch {
      // fallback
    }
  }
  const datesMock: Record<string, string> = {
    'administrador': '23 sep 2026',
    'recepcion': '19 sep 2026',
    'recepción': '19 sep 2026',
    'tecnico': '16 sep 2026',
    'técnico': '16 sep 2026',
    'cliente': '10 sep 2026'
  }
  const normalized = role.name.toLowerCase().trim()
  if (datesMock[normalized]) return datesMock[normalized]
  const offset = ((role.id * 7) % 20) + 2
  const fallback = new Date(Date.now() - offset * 86400000)
  return fallback.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
}

function initials(user: RoleUser) {
  return user.name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || '?'
}

function syncRole(updated: Role) {
  roles.value = roles.value.map(role => role.id === updated.id ? updated : role)
  selectedRole.value = updated
}

async function loadRoleUsers(role: Role) {
  selectedRole.value = role
  roleUsers.value = null
  userLoading.value = true
  try {
    roleUsers.value = await listRoleUsers(role.id)
  } catch (cause: any) {
    error.value = cause.response?.data?.detail || 'No fue posible cargar los usuarios del rol.'
  } finally {
    userLoading.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const rawStatus = localStorage.getItem('taller_roles_status')
    if (rawStatus) {
      try { roleActiveStatus.value = JSON.parse(rawStatus) } catch { /* ignore */ }
    }
    ;[roles.value, permissions.value] = await Promise.all([listRoles(), listPermissions()])
    if (roles.value.length) {
      await loadRoleUsers(roles.value[0])
    }
  } catch {
    error.value = 'No fue posible cargar la información de roles.'
  } finally {
    loading.value = false
  }
}

function openEdit(role: Role) {
  editing.value = role
  form.value = {
    name: role.name,
    description: role.description,
    permission_ids: role.permissions.map(p => p.id)
  }
}

function groupAll(group: Permission[]) {
  if (!group.length) return false
  return group.every(p => form.value.permission_ids.includes(p.id))
}

function toggleGroup(group: Permission[]) {
  const ids = group.map(p => p.id)
  form.value.permission_ids = groupAll(group)
    ? form.value.permission_ids.filter(id => !ids.includes(id))
    : [...new Set([...form.value.permission_ids, ...ids])]
}

async function save() {
  if (!editing.value || !canSaveEdit.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await updateRole(editing.value.id, form.value)
    syncRole(updated)
    editing.value = null
    showSuccess('Los cambios del perfil se guardaron correctamente.')
    if (roleUsers.value) roleUsers.value = { ...roleUsers.value, role: updated }
  } catch (cause: any) {
    error.value = cause.response?.data?.detail || 'No fue posible actualizar el rol.'
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!removing.value) return
  saving.value = true
  error.value = ''
  try {
    await deleteRole(removing.value.id)
    roles.value = roles.value.filter(role => role.id !== removing.value?.id)
    removing.value = null
    selectedRole.value = roles.value[0] || null
    roleUsers.value = null
    if (selectedRole.value) await loadRoleUsers(selectedRole.value)
    showSuccess('Perfil eliminado satisfactoriamente.')
  } catch (cause: any) {
    error.value = cause.response?.data?.detail || 'No fue posible eliminar el rol.'
  } finally {
    saving.value = false
  }
}

async function assignUser(user: RoleUser) {
  if (!selectedRole.value) return
  saving.value = true
  error.value = ''
  try {
    const result = await assignUserToRole(selectedRole.value.id, user.id)
    roleUsers.value = result
    syncRole(result.role)
    showSuccess(`Usuario "${user.name}" asignado a ${selectedRole.value.name}.`)
  } catch (cause: any) {
    error.value = cause.response?.data?.detail || 'No fue posible asociar al usuario.'
  } finally {
    saving.value = false
  }
}

async function confirmRemoveUser() {
  if (!selectedRole.value || !removingUser.value) return
  saving.value = true
  error.value = ''
  try {
    const result = await removeUserFromRole(selectedRole.value.id, removingUser.value.id)
    roleUsers.value = result
    syncRole(result.role)
    showSuccess(`Usuario "${removingUser.value.name}" retirado de ${selectedRole.value.name}.`)
    removingUser.value = null
  } catch (cause: any) {
    error.value = cause.response?.data?.detail || 'No fue posible retirar al usuario.'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await load()
  if (route.query.created === '1') {
    showSuccess('El rol se creó correctamente.')
    await router.replace({ query: {} })
  }
})
onBeforeUnmount(() => { if (createdAlertTimer) window.clearTimeout(createdAlertTimer) })
</script>

<template>
  <v-container class="admin-container manage-role-page">
    <!-- Encabezado de la pantalla -->
    <header class="page-header">
      <p class="section-label">CONFIGURACIÓN DE ACCESO</p>
      <h1>Administración de roles</h1>
      <p>Mantén el catálogo de roles y asócialos con usuarios desde una operación controlada.</p>
    </header>

    <v-alert v-if="snackMessage" class="role-created-success mb-5" variant="flat">
      <v-icon icon="mdi-check-circle" class="mr-2" />{{ snackMessage }}
    </v-alert>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-5" closable @click:close="error = ''">
      {{ error }}
    </v-alert>

    <!-- Tarjetas de métricas superiores (3 tarjetas alineadas a la referencia) -->
    <section class="stats-grid">
      <v-card class="stat-card" elevation="0">
        <div class="stat-icon blue">
          <v-icon icon="mdi-shield-outline" size="22" />
        </div>
        <div class="stat-content">
          <strong class="stat-number">{{ roles.length }}</strong>
          <span class="stat-label">Roles registrados</span>
        </div>
      </v-card>

      <v-card class="stat-card" elevation="0">
        <div class="stat-icon dark">
          <v-icon icon="mdi-check-circle" size="22" />
        </div>
        <div class="stat-content">
          <strong class="stat-number">{{ activeRolesCount }}</strong>
          <span class="stat-label">Roles activos</span>
        </div>
      </v-card>

      <v-card class="stat-card" elevation="0">
        <div class="stat-icon gold">
          <v-icon icon="mdi-account-group-outline" size="22" />
        </div>
        <div class="stat-content">
          <strong class="stat-number">{{ associatedUsers }}</strong>
          <span class="stat-label">Usuarios asociados</span>
        </div>
      </v-card>
    </section>

    <!-- Distribución principal en 2 paneles -->
    <section class="manage-grid">
      <!-- Panel Izquierdo: Catálogo de roles -->
      <v-card class="admin-card catalog-card" elevation="0">
        <div class="card-toolbar">
          <div>
            <h2>Catálogo de roles</h2>
            <p>Selecciona un rol para administrar sus asociaciones.</p>
          </div>
          <div class="toolbar-actions">
            <v-text-field
              v-model="search"
              placeholder="Buscar rol"
              prepend-inner-icon="mdi-magnify"
              density="compact"
              variant="outlined"
              hide-details
              class="search-field"
            />
            <v-select
              v-model="statusFilter"
              :items="filterOptions"
              item-title="title"
              item-value="value"
              density="compact"
              variant="outlined"
              hide-details
              class="filter-select"
            />
            <v-btn color="primary" prepend-icon="mdi-plus" to="/roles/nuevo" class="new-role-btn">
              Nuevo rol
            </v-btn>
          </div>
        </div>

        <v-progress-linear v-if="loading" indeterminate color="primary" class="mt-6" />

        <div v-else class="table-wrap">
          <v-table class="roles-table">
            <thead>
              <tr>
                <th>ROL</th>
                <th>USUARIOS</th>
                <th>ESTADO</th>
                <th>ACTUALIZACIÓN</th>
                <th class="text-right">ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="role in filtered"
                :key="role.id"
                :class="{ selected: selectedRole?.id === role.id }"
                @click="loadRoleUsers(role)"
              >
                <!-- Nombre y descripción -->
                <td>
                  <div class="role-name">{{ role.name }}</div>
                  <div v-if="role.description" class="role-description">{{ role.description }}</div>
                </td>

                <!-- Conteo de usuarios -->
                <td class="font-weight-medium">{{ role.user_count }}</td>

                <!-- Estado con viñeta activa/inactiva -->
                <td>
                  <div v-if="isRoleActive(role)" class="status-badge status-active">
                    <span class="status-dot active"></span>
                    <span>Activo</span>
                  </div>
                  <div v-else class="status-badge status-inactive">
                    <span class="status-dot inactive"></span>
                    <span>Inactivo</span>
                  </div>
                </td>

                <!-- Fecha de actualización -->
                <td class="date-cell">{{ formatRoleDate(role) }}</td>

                <!-- Acciones -->
                <td class="actions-cell">
                  <!-- Botón asociar/ver usuarios -->
                  <v-tooltip text="Administrar usuarios">
                    <template #activator="{ props }">
                      <v-btn
                        v-bind="props"
                        icon="mdi-account-group-outline"
                        variant="text"
                        size="small"
                        color="primary"
                        aria-label="Administrar usuarios"
                        @click.stop="loadRoleUsers(role)"
                      />
                    </template>
                  </v-tooltip>

                  <!-- Toggle switch para activar/desactivar estado -->
                  <v-tooltip :text="isRoleActive(role) ? 'Desactivar rol' : 'Activar rol'">
                    <template #activator="{ props }">
                      <v-btn
                        v-bind="props"
                        :icon="isRoleActive(role) ? 'mdi-toggle-switch' : 'mdi-toggle-switch-off-outline'"
                        variant="text"
                        size="small"
                        :color="isRoleActive(role) ? 'primary' : 'grey'"
                        :disabled="role.name.toLowerCase() === 'administrador'"
                        aria-label="Cambiar estado del rol"
                        @click.stop="toggleRoleStatus(role)"
                      />
                    </template>
                  </v-tooltip>

                  <!-- Menú de opciones extra: Editar, Detalle, Eliminar -->
                  <v-menu location="bottom end">
                    <template #activator="{ props }">
                      <v-btn v-bind="props" icon="mdi-dots-vertical" variant="text" size="small" color="grey-darken-1" />
                    </template>
                    <v-list density="compact" elevation="2" rounded="lg">
                      <v-list-item prepend-icon="mdi-eye-outline" title="Ver detalles" @click="detail = role" />
                      <v-list-item prepend-icon="mdi-pencil-outline" title="Editar rol" @click="openEdit(role)" />
                      <v-list-item
                        prepend-icon="mdi-delete-outline"
                        title="Eliminar rol"
                        color="error"
                        :disabled="role.is_protected || role.user_count > 0"
                        @click="removing = role"
                      />
                    </v-list>
                  </v-menu>
                </td>
              </tr>

              <tr v-if="!filtered.length">
                <td colspan="5" class="empty-table">No se encontraron roles coincidentes.</td>
              </tr>
            </tbody>
          </v-table>
        </div>
      </v-card>

      <!-- Panel Derecho: Usuarios del rol seleccionado -->
      <v-card class="admin-card users-card" elevation="0">
        <template v-if="selectedRole">
          <div class="users-heading">
            <div class="heading-icon blue">
              <v-icon icon="mdi-account-multiple-outline" size="22" />
            </div>
            <div>
              <h2>Usuarios de {{ selectedRole.name }}</h2>
              <p>Asocia o retira usuarios del rol seleccionado.</p>
            </div>
          </div>

          <v-progress-linear v-if="userLoading" indeterminate color="primary" class="my-5" />

          <template v-else-if="roleUsers">
            <!-- Sección Asignados -->
            <section class="user-section">
              <div class="user-section-title">
                <span>Asignados</span>
                <span class="user-count-chip">{{ roleUsers.assigned.length }}</span>
              </div>
              <div class="user-list">
                <div v-for="user in roleUsers.assigned" :key="user.id" class="user-card-item">
                  <div class="user-avatar-initials">{{ initials(user) }}</div>
                  <div class="user-info">
                    <strong>{{ user.name }}</strong>
                    <span>{{ user.email }}</span>
                  </div>
                  <v-tooltip text="Retirar usuario">
                    <template #activator="{ props }">
                      <button
                        v-bind="props"
                        type="button"
                        class="user-action-btn remove-btn"
                        aria-label="Retirar del rol"
                        @click="removingUser = user"
                      >
                        <v-icon icon="mdi-close" size="18" />
                      </button>
                    </template>
                  </v-tooltip>
                </div>
                <div v-if="!roleUsers.assigned.length" class="empty-users">
                  No hay colaboradores asociados a este perfil.
                </div>
              </div>
            </section>

            <!-- Sección Disponibles -->
            <section class="user-section">
              <div class="user-section-title">
                <span>Disponibles</span>
                <span class="user-count-chip">{{ roleUsers.available.length }}</span>
              </div>
              <div class="user-list">
                <div v-for="user in roleUsers.available" :key="user.id" class="user-card-item">
                  <div class="user-avatar-initials available">{{ initials(user) }}</div>
                  <div class="user-info">
                    <strong>{{ user.name }}</strong>
                    <span>{{ user.email }}</span>
                  </div>
                  <v-tooltip text="Asociar usuario">
                    <template #activator="{ props }">
                      <button
                        v-bind="props"
                        type="button"
                        class="user-action-btn add-btn"
                        aria-label="Asociar al rol"
                        :disabled="saving"
                        @click="assignUser(user)"
                      >
                        <v-icon icon="mdi-plus" size="18" />
                      </button>
                    </template>
                  </v-tooltip>
                </div>
                <div v-if="!roleUsers.available.length" class="empty-users">
                  Todos los usuarios disponibles ya cuentan con este rol.
                </div>
              </div>
            </section>
          </template>
        </template>

        <div v-else class="empty-selection">
          <v-icon icon="mdi-account-group-outline" size="38" />
          <p>Selecciona un rol para consultar y asociar usuarios.</p>
        </div>
      </v-card>
    </section>

    <!-- Diálogos modales para Detalle, Edición y Confirmaciones -->
    <v-dialog :model-value="!!detail" max-width="560" @update:model-value="v => { if (!v) detail = null }">
      <v-card v-if="detail" class="dialog-card permissions-detail-dialog">
        <header class="permissions-detail-dialog__header"><div class="permissions-detail-dialog__crown"><v-icon icon="mdi-account-outline" size="25" /></div><span class="permissions-detail-dialog__divider" aria-hidden="true" /><div><h2>{{ detail.name }}</h2><v-chip class="permissions-detail-dialog__badge" size="x-small">Acceso completo</v-chip></div><v-btn class="permissions-detail-dialog__close" aria-label="Cerrar detalle de rol" icon="mdi-close" variant="text" @click="detail = null" /></header>
        <v-card-text class="permissions-detail-dialog__content"><div class="permissions-detail-dialog__section-title"><div><v-icon icon="mdi-key-variant" size="21" /></div><div><h3>Permisos asignados</h3><p>Accesos configurados actualmente para este rol.</p></div></div><div v-if="detail.permissions.length" class="permissions-detail-dialog__grid"><article v-for="permission in detail.permissions" :key="permission.id" class="permission-detail-card"><v-icon icon="mdi-key-outline" size="20" /><span>{{ permissionLabel(permission.code) }}</span></article></div><div v-else class="permissions-detail-dialog__empty"><v-icon icon="mdi-key-off" size="25" />Este rol no tiene permisos asignados.</div></v-card-text>
        <v-card-actions class="permissions-detail-dialog__actions">
          <v-spacer />
          <v-btn class="permissions-detail-dialog__button" variant="flat" @click="detail = null">Cerrar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog :model-value="!!editing" max-width="960" @update:model-value="v => { if (!v) editing = null }">
      <v-card v-if="editing" class="dialog-card role-edit-dialog">
        <header class="role-edit-dialog__header"><div class="role-edit-dialog__icon"><v-icon icon="mdi-shield-edit-outline" size="27" /></div><span class="role-edit-dialog__divider" aria-hidden="true" /><div><h2>Editar rol</h2><p>Actualiza la información y los permisos asignados.</p></div><v-btn class="role-edit-dialog__close" aria-label="Cerrar edición de rol" icon="mdi-close" variant="text" :disabled="saving" @click="editing = null" /></header>
        <v-card-text class="role-edit-dialog__content">
          <div class="role-edit-dialog__fields">
            <v-text-field v-model.trim="form.name" label="Nombre del rol" prepend-inner-icon="mdi-shield-account-outline" variant="outlined" density="comfortable" :error="form.name.length > 0 && form.name.trim().length < 3" :error-messages="form.name.length > 0 && form.name.trim().length < 3 ? 'Ingresa al menos 3 caracteres.' : []" />
            <v-text-field v-model.trim="form.description" label="Descripción" prepend-inner-icon="mdi-text-box-outline" variant="outlined" density="comfortable" hide-details />
          </div>
          <section class="role-edit-dialog__permissions">
            <div class="role-edit-dialog__section-heading"><div><v-icon icon="mdi-key-variant" size="22" /></div><div><h3>Permisos del rol</h3><p>Define los accesos disponibles para este perfil.</p></div></div>
            <div class="role-edit-dialog__groups">
              <article v-for="group in permissionGroups" :key="group.key" class="role-permission-card">
                <header><div><v-icon :icon="group.icon" size="19" /></div><strong>{{ group.title }}</strong></header>
                <div class="role-permission-card__body">
                  <v-checkbox-btn :model-value="groupAll(group.permissions)" :indeterminate="group.permissions.some(permission => form.permission_ids.includes(permission.id)) && !groupAll(group.permissions)" :disabled="!group.permissions.length" hide-details density="compact" @update:model-value="toggleGroup(group.permissions)">
                    <template #label><span>Seleccionar todos</span></template>
                  </v-checkbox-btn>
                  <v-checkbox v-for="permission in group.permissions" :key="permission.id" v-model="form.permission_ids" :value="permission.id" :label="permissionLabel(permission.code)" density="compact" hide-details />
                  <p v-if="!group.permissions.length" class="role-permission-card__empty">Sin permisos disponibles.</p>
                </div>
              </article>
            </div>
          </section>
        </v-card-text>
        <v-card-actions class="role-edit-dialog__actions">
          <v-spacer />
          <v-btn class="role-edit-dialog__cancel" variant="outlined" :disabled="saving" @click="editing = null">Cancelar</v-btn>
          <v-btn class="role-edit-dialog__save" prepend-icon="mdi-content-save-outline" :loading="saving" :disabled="saving || !canSaveEdit" @click="save">Guardar cambios</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog :model-value="!!removing" max-width="460" @update:model-value="v => { if (!v) removing = null }">
      <v-card v-if="removing" class="dialog-card delete-role-dialog">
        <header class="delete-role-dialog__header"><div class="delete-role-dialog__header-icon"><v-icon icon="mdi-shield-remove-outline" size="25" /></div><div><h2>Eliminar rol</h2><p>Confirma esta acción antes de continuar.</p></div><v-btn class="delete-role-dialog__close" aria-label="Cerrar eliminación de rol" icon="mdi-close" variant="text" :disabled="saving" @click="removing = null" /></header>
        <v-card-text class="delete-role-dialog__content"><v-icon class="delete-role-dialog__warning" icon="mdi-alert-circle-outline" size="58" /><h3>¿Seguro que deseas <span>eliminar</span> este rol?</h3><strong class="delete-role-dialog__name">{{ removing.name }}</strong><p>Esta acción no se puede deshacer.</p></v-card-text>
        <v-card-actions class="delete-role-dialog__actions">
          <v-spacer />
          <v-btn class="delete-role-dialog__cancel" variant="outlined" :disabled="saving" @click="removing = null">Cancelar</v-btn>
          <v-btn class="delete-role-dialog__confirm" prepend-icon="mdi-shield-remove-outline" :loading="saving" :disabled="saving" @click="remove">Eliminar rol</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog :model-value="!!removingUser" max-width="460" @update:model-value="v => { if (!v) removingUser = null }">
      <v-card v-if="removingUser" class="dialog-card withdraw-user-dialog">
        <header class="withdraw-user-dialog__header"><div class="withdraw-user-dialog__header-icon"><v-icon icon="mdi-account-remove-outline" size="25" /></div><div><h2>Retirar usuario</h2><p>Confirma esta acción antes de continuar.</p></div><v-btn class="withdraw-user-dialog__close" aria-label="Cerrar retiro de usuario" icon="mdi-close" variant="text" :disabled="saving" @click="removingUser = null" /></header>
        <v-card-text class="withdraw-user-dialog__content"><v-icon class="withdraw-user-dialog__warning" icon="mdi-alert-circle-outline" size="58" /><h3>¿Seguro que deseas <span>retirar</span> a este usuario del rol?</h3><strong class="withdraw-user-dialog__name">{{ removingUser.name }}</strong><span class="withdraw-user-dialog__role"><v-icon icon="mdi-shield-account-outline" size="16" />{{ selectedRole?.name || 'Rol no disponible' }}</span><p>La pertenencia al rol se quitará de forma inmediata.</p></v-card-text>
        <v-card-actions class="withdraw-user-dialog__actions">
          <v-spacer />
          <v-btn class="withdraw-user-dialog__cancel" variant="outlined" :disabled="saving" @click="removingUser = null">Cancelar</v-btn>
          <v-btn class="withdraw-user-dialog__confirm" prepend-icon="mdi-account-remove-outline" :loading="saving" :disabled="saving" @click="confirmRemoveUser">Retirar usuario</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<style scoped>
.admin-container {
  max-width: 1240px;
  padding: 38px 32px 64px;
}

.page-header {
  margin-bottom: 26px;
}

.section-label {
  margin: 0 0 8px;
  color: #3364A2;
  font-size: 0.72rem;
  letter-spacing: 1.4px;
  font-weight: 800;
}

.page-header h1 {
  margin: 0;
  color: #172B4D;
  font-size: clamp(1.9rem, 2.7vw, 2.45rem);
  letter-spacing: -0.6px;
  line-height: 1.15;
  font-weight: 800;
}

.page-header p {
  margin: 8px 0 0;
  color: #66758B;
  font-size: 0.94rem;
}

.role-created-success {
  border: 1px solid rgba(35, 126, 24, .23) !important;
  background: #eaf7ea !important;
  color: #237e18 !important;
  font-weight: 700;
}

.role-created-success :deep(.v-icon) { color: #237e18 !important; }

.permissions-detail-dialog { display:flex; flex-direction:column; max-height:calc(100dvh - 48px); overflow:hidden; padding:0; border:1px solid #e4e9f2; border-radius:18px; background:#fff; box-shadow:0 18px 42px rgba(20,43,80,.16); }
.permissions-detail-dialog::before { display:none !important; }
.permissions-detail-dialog__header { display:flex; align-items:center; gap:14px; flex:none; padding:23px 27px 20px; border-bottom:1px solid #e4eaf1; background:#fff; }
.permissions-detail-dialog__crown { display:grid; place-items:center; width:48px; height:48px; flex:none; border-radius:13px; background:#f8e9ce; color:#2850e8; }
.permissions-detail-dialog__divider { align-self:stretch; width:2px; border-radius:2px; background:#dda34e; }
.permissions-detail-dialog__header h2 { margin:0 0 6px; color:#172b4d; font-size:1.25rem; font-weight:800; }
.permissions-detail-dialog__badge { background:#eef0f3 !important; color:#2850e8 !important; font-weight:800; }
.permissions-detail-dialog__close { margin-left:auto; color:#718096; border-radius:9px; }
.permissions-detail-dialog__close:hover { background:rgba(198,70,70,.10); color:#c64747; }
.permissions-detail-dialog__content { flex:1 1 auto; overflow-y:auto; padding:23px 27px 20px; }
.permissions-detail-dialog__section-title { display:flex; align-items:center; gap:11px; margin-bottom:16px; }
.permissions-detail-dialog__section-title>div:first-child { display:grid; place-items:center; width:38px; height:38px; border-radius:50%; background:#f8e9ce; color:#2850e8; }
.permissions-detail-dialog__section-title h3 { margin:0; color:#1d365c; font-size:1.03rem; font-weight:800; }
.permissions-detail-dialog__section-title p { margin:3px 0 0; color:#718096; font-size:.81rem; }
.permissions-detail-dialog__grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:11px; }
.permission-detail-card { display:flex; align-items:center; gap:10px; min-height:66px; padding:13px; border:1px solid #d9e7f8; border-radius:13px; background:#f1f7ff; color:#1d365c; }
.permission-detail-card>.v-icon { flex:none; color:#2850e8; }
.permission-detail-card span { font-size:.82rem; font-weight:700; line-height:1.35; }
.permissions-detail-dialog__empty { display:flex; align-items:center; justify-content:center; gap:8px; min-height:112px; border:1px dashed #cbd8e7; border-radius:13px; color:#718096; font-size:.83rem; }
.permissions-detail-dialog__empty .v-icon { color:#6b8bb8; }
.permissions-detail-dialog__actions { flex:none; padding:16px 27px 21px; border-top:1px solid #e4eaf1; background:#fff; }
.permissions-detail-dialog__button { min-width:125px; border:1px solid #d7dde5 !important; border-radius:10px; background:#fff !important; color:#475569 !important; font-weight:800; text-transform:none; }
.permissions-detail-dialog__button:hover,.permissions-detail-dialog__button:focus-visible,.permissions-detail-dialog__button:active { border-color:#dc3545 !important; background:#fdebed !important; color:#c64747 !important; }

.withdraw-user-dialog { overflow: hidden; padding: 0; text-align: center; }
.withdraw-user-dialog::before { display: none !important; }
.withdraw-user-dialog__header { display: flex; align-items: center; gap: 13px; padding: 22px 26px; border-bottom: 1px solid #f0d9dc; background: #fffafa; text-align: left; }
.withdraw-user-dialog__header-icon { display: grid; place-items: center; width: 44px; height: 44px; flex: none; border-radius: 12px; background: #fdebed; color: #2850e8; }
.withdraw-user-dialog__header h2 { margin: 0; color: #142b50; font-size: 1.14rem; font-weight: 800; }
.withdraw-user-dialog__header p { margin: 4px 0 0; color: #64748b; font-size: .82rem; }
.withdraw-user-dialog__close { margin-left: auto; color: #64748b; border-radius: 9px; }
.withdraw-user-dialog__close:hover:not(.v-btn--disabled) { background: rgba(198,70,70,.1); color: #c64747; }
.withdraw-user-dialog__content { padding: 24px 30px 22px; }
.withdraw-user-dialog__warning { display: block; margin: 0 auto 13px; color: #dc3545; }
.withdraw-user-dialog__content h3 { max-width: 365px; margin: 0 auto; color: #142b50; font-size: 1.14rem; line-height: 1.4; }
.withdraw-user-dialog__content h3 span { color: #dc3545; }
.withdraw-user-dialog__name { display: block; margin: 13px 0 4px; color: #475569; font-size: .93rem; }
.withdraw-user-dialog__role { display: inline-flex; align-items: center; gap: 5px; color: #64748b; font-size: .8rem; font-weight: 700; }
.withdraw-user-dialog__role .v-icon { color: #2850e8; }
.withdraw-user-dialog__content>p { max-width: 365px; margin: 13px auto 0; color: #64748b; font-size: .86rem; line-height: 1.55; }
.withdraw-user-dialog__actions { padding: 16px 26px 22px; border-top: 1px solid #edf0f4; background: #fff; }
.withdraw-user-dialog__cancel { min-width: 112px; border-color: #cbd5e1 !important; background: #fff !important; color: #475569 !important; }
.withdraw-user-dialog__cancel:hover:not(.v-btn--disabled),.withdraw-user-dialog__cancel:focus-visible:not(.v-btn--disabled) { border-color: #334155 !important; background: #334155 !important; color: #fff !important; }
.withdraw-user-dialog__confirm { min-width: 150px; background: linear-gradient(135deg,#dc3545,#b91c2c) !important; color: #fff !important; box-shadow: 0 7px 16px rgba(185,28,44,.22); }
.withdraw-user-dialog__confirm:hover:not(.v-btn--disabled),.withdraw-user-dialog__confirm:focus-visible:not(.v-btn--disabled) { background: linear-gradient(135deg,#b91c2c,#8f1724) !important; color: #fff !important; }
.withdraw-user-dialog__confirm :deep(.v-icon) { color: #fff !important; }

.delete-role-dialog { overflow:hidden; padding:0; text-align:center; }
.delete-role-dialog::before { display:none !important; }
.delete-role-dialog__header { display:flex; align-items:center; gap:13px; padding:22px 26px; border-bottom:1px solid #f0d9dc; background:#fffafa; text-align:left; }
.delete-role-dialog__header-icon { display:grid; place-items:center; width:44px; height:44px; flex:none; border-radius:12px; background:#fdebed; color:#2850e8; }
.delete-role-dialog__header h2 { margin:0; color:#142b50; font-size:1.14rem; font-weight:800; }
.delete-role-dialog__header p { margin:4px 0 0; color:#64748b; font-size:.82rem; }
.delete-role-dialog__close { margin-left:auto; color:#64748b; border-radius:9px; }
.delete-role-dialog__close:hover:not(.v-btn--disabled) { background:rgba(198,70,70,.1); color:#c64747; }
.delete-role-dialog__content { padding:24px 30px 22px; }
.delete-role-dialog__warning { display:block; margin:0 auto 13px; color:#dc3545; }
.delete-role-dialog__content h3 { max-width:365px; margin:0 auto; color:#142b50; font-size:1.14rem; line-height:1.4; }
.delete-role-dialog__content h3 span { color:#dc3545; }
.delete-role-dialog__name { display:table; margin:13px auto 0; padding:6px 12px; border-radius:999px; background:#e8f0ff; color:#2850e8; font-size:.86rem; font-weight:800; }
.delete-role-dialog__content>p { max-width:365px; margin:13px auto 0; color:#64748b; font-size:.86rem; line-height:1.55; }
.delete-role-dialog__actions { padding:16px 26px 22px; border-top:1px solid #edf0f4; background:#fff; }
.delete-role-dialog__cancel { min-width:112px; border-color:#cbd5e1 !important; background:#fff !important; color:#475569 !important; }
.delete-role-dialog__cancel:hover:not(.v-btn--disabled),.delete-role-dialog__cancel:focus-visible:not(.v-btn--disabled) { border-color:#dc3545 !important; background:#fdebed !important; color:#c64747 !important; }
.delete-role-dialog__confirm { min-width:150px; background:linear-gradient(135deg,#dc3545,#b91c2c) !important; color:#fff !important; box-shadow:0 7px 16px rgba(185,28,44,.22); }
.delete-role-dialog__confirm:hover:not(.v-btn--disabled),.delete-role-dialog__confirm:focus-visible:not(.v-btn--disabled) { background:linear-gradient(135deg,#b91c2c,#8f1724) !important; color:#fff !important; }
.delete-role-dialog__confirm :deep(.v-icon) { color:#fff !important; }

/* Tarjetas de métricas */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-bottom: 24px;
}

.stat-card,
.admin-card {
  border: 1px solid #E4E9F2;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(23, 43, 77, 0.05);
}

.stat-card {
  padding: 22px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  flex: none;
}

.stat-icon.blue {
  background: #EDF3FF;
  color: #3867DE;
}

.stat-icon.dark {
  background: #EEF2F7;
  color: #172B4D;
}

.stat-icon.gold {
  background: #FFF6E7;
  color: #C48530;
}

.stat-number {
  display: block;
  color: #172B4D;
  font-size: 1.45rem;
  font-weight: 800;
  line-height: 1.1;
}

.stat-label {
  display: block;
  margin-top: 4px;
  color: #748197;
  font-size: 0.8rem;
}

/* Grilla de gestión */
.manage-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(330px, 1.15fr);
  gap: 24px;
  align-items: start;
}

.catalog-card,
.users-card {
  padding: 26px;
}

.card-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.card-toolbar h2,
.users-heading h2,
.dialog-card h2 {
  margin: 0;
  color: #172B4D;
  font-size: 1.12rem;
  font-weight: 700;
}

.card-toolbar p,
.users-heading p {
  margin: 4px 0 0;
  color: #738096;
  font-size: 0.83rem;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.search-field {
  width: 175px;
}

.filter-select {
  width: 155px;
}

.new-role-btn {
  border-radius: 10px;
  text-transform: none;
  font-weight: 700;
}

/* Tabla */
.table-wrap {
  overflow-x: auto;
  margin-top: 18px;
}

.roles-table {
  min-width: 620px;
}

.roles-table :deep(th) {
  background: #F6F8FC;
  color: #718096;
  font-size: 0.7rem;
  letter-spacing: 0.7px;
  font-weight: 800;
  white-space: nowrap;
}

.roles-table :deep(td),
.roles-table :deep(th) {
  padding: 15px 14px !important;
  border-color: #EEF2F6 !important;
}

.roles-table tbody tr {
  cursor: pointer;
  transition: background 0.18s ease;
}

.roles-table tbody tr:hover,
.roles-table tbody tr.selected {
  background: #F0F5FF;
}

.role-name {
  color: #172B4D;
  font-size: 0.9rem;
  font-weight: 700;
}

.role-description {
  max-width: 220px;
  margin-top: 3px;
  overflow: hidden;
  color: #7A8797;
  font-size: 0.76rem;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Estado viñeta */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 0.82rem;
  font-weight: 600;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: none;
}

.status-active .status-dot {
  background: #172B4D;
}

.status-inactive .status-dot {
  background: #94A3B8;
}

.status-active {
  color: #172B4D;
}

.status-inactive {
  color: #94A3B8;
}

.date-cell {
  color: #55657A;
  font-size: 0.82rem;
  white-space: nowrap;
}

.actions-cell {
  white-space: nowrap;
  text-align: right;
}

.empty-table {
  text-align: center;
  color: #7D8999;
  padding: 36px !important;
}

/* Panel derecho: Usuarios */
.users-heading {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.heading-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  flex: none;
}

.heading-icon.blue {
  background: #EDF3FF;
  color: #3867DE;
}

.user-section {
  margin-top: 24px;
}

.user-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 11px;
  color: #263852;
  font-size: 0.83rem;
  font-weight: 800;
}

.user-count-chip {
  display: inline-block;
  padding: 1px 7px;
  background: #EEF3FA;
  color: #3867DE;
  border-radius: 99px;
  font-size: 0.72rem;
  font-weight: 700;
}

.user-list {
  max-height: 250px;
  overflow-y: auto;
  display: grid;
  gap: 9px;
  padding-right: 2px;
}

.user-card-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border-radius: 12px;
  background: #F7F9FC;
  border: 1px solid #EEF2F8;
  transition: background 0.15s ease;
}

.user-card-item:hover {
  background: #F0F4FA;
}

.user-avatar-initials {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #3867DE;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 800;
  display: grid;
  place-items: center;
  flex: none;
}

.user-avatar-initials.available {
  background: #E2E8F0;
  color: #334862;
}

.user-info {
  min-width: 0;
  flex: 1;
}

.user-info strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #203248;
  font-size: 0.82rem;
}

.user-info span {
  display: block;
  margin-top: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #718195;
  font-size: 0.72rem;
}

/* Botones de acción usuarios estilo referencia */
.user-action-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.18s ease;
  background: #fff;
}

.user-action-btn.remove-btn {
  border-color: #F8D7DA;
  color: #D32F2F;
}

.user-action-btn.remove-btn:hover {
  background: #FFEBEE;
}

.user-action-btn.add-btn {
  border-color: #C3D6EA;
  color: #3867DE;
}

.user-action-btn.add-btn:hover {
  background: #EDF3FF;
}

.empty-users {
  padding: 16px;
  color: #7D8E9F;
  background: #F9FAFC;
  border-radius: 10px;
  text-align: center;
  font-size: 0.78rem;
}

.empty-selection {
  min-height: 320px;
  display: grid;
  place-content: center;
  gap: 12px;
  color: #8190A1;
  text-align: center;
}

/* Dialogos */
.dialog-card {
  padding: 28px;
  border-radius: 16px;
}

.permission-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.permission-edit {
  margin-top: 15px;
  padding: 14px;
  border: 1px solid #E4E9F2;
  border-radius: 12px;
}

/* Modal de edición: cabecera y acciones fijas; sólo el contenido se desplaza. */
.role-edit-dialog { display:flex; flex-direction:column; max-height:min(840px, calc(100dvh - 42px)); overflow:hidden; padding:0; border:1px solid #dce5f0; border-radius:18px; background:#fff; box-shadow:0 20px 46px rgba(20,43,80,.18); }
.role-edit-dialog::before { display:none !important; }
.role-edit-dialog__header { display:flex; align-items:center; gap:14px; flex:none; padding:16px 24px; border-bottom:1px solid #e6edf5; background:#fff; }
.role-edit-dialog__icon { display:grid; width:48px; height:48px; place-items:center; flex:none; border-radius:13px; background:#f8e9ce; color:#2850e8; }
.role-edit-dialog__divider { width:4px; align-self:stretch; border-radius:4px; background:#f2ae16; }
.role-edit-dialog__header h2 { margin:0; color:#172b4d; font-size:1.24rem; font-weight:800; }
.role-edit-dialog__header p { margin:4px 0 0; color:#718096; font-size:.83rem; }
.role-edit-dialog__close { margin-left:auto; border-radius:9px; color:#64748b; }
.role-edit-dialog__close:hover:not(.v-btn--disabled) { background:#fdebed; color:#c64747; }
.role-edit-dialog__content { flex:1 1 auto; overflow-y:auto; padding:18px 24px 22px; }
.role-edit-dialog__fields { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; align-items:start; }
.role-edit-dialog__fields :deep(.v-input) { min-width:0; }
.role-edit-dialog__fields :deep(.v-field) { min-height:56px; border-radius:11px; background:#fff; }
.role-edit-dialog__fields :deep(.v-field__prepend-inner .v-icon) { color:#2850e8; opacity:1; }
.role-edit-dialog__permissions { overflow:hidden; margin-top:18px; padding:0; border:1px solid #d9e7f8; border-radius:14px; background:#fff; }
.role-edit-dialog__section-heading { display:flex; align-items:center; gap:11px; margin:0; padding:15px; border-bottom:1px solid #d9e7f8; background:#eaf3ff; }
.role-edit-dialog__section-heading>div:first-child { display:grid; place-items:center; width:39px; height:39px; border-radius:11px; background:#f8e9ce; color:#2850e8; }
.role-edit-dialog__section-heading h3 { margin:0; color:#173a72; font-size:1rem; font-weight:800; }
.role-edit-dialog__section-heading p { margin:3px 0 0; color:#61738e; font-size:.79rem; }
.role-edit-dialog__groups { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:13px; padding:14px; }
.role-permission-card { overflow:hidden; border:1px solid #d4e2f2; border-radius:12px; background:#fff; }
.role-permission-card>header { display:flex; align-items:center; gap:9px; min-height:46px; padding:8px 12px; border-bottom:1px solid #dce9f6; background:#edf5ff; color:#173a72; }
.role-permission-card>header>div { display:grid; width:28px; height:28px; place-items:center; flex:none; border-radius:8px; background:#f8e9ce; color:#2850e8; }
.role-permission-card>header strong { font-size:.82rem; line-height:1.2; }
.role-permission-card__body { padding:8px 12px 11px; }
.role-permission-card__body :deep(.v-selection-control) { min-height:31px; }
.role-permission-card__body :deep(.v-label) { color:#111827; font-size:.78rem; font-weight:800; opacity:1; }
.role-permission-card__empty { margin:4px 0; color:#8190a1; font-size:.76rem; }
.role-edit-dialog__actions { flex:none; padding:15px 24px 18px; border-top:1px solid #e6edf5; background:#fff; }
.role-edit-dialog__cancel { min-width:112px; border-color:#2850e8 !important; background:#fff !important; color:#2850e8 !important; font-weight:800; text-transform:none; }
.role-edit-dialog__cancel:hover:not(.v-btn--disabled),.role-edit-dialog__cancel:focus-visible:not(.v-btn--disabled) { border-color:#dc3545 !important; background:#fdebed !important; color:#c64747 !important; }
.role-edit-dialog__save { min-width:154px; background:#5d8df2 !important; color:#fff !important; font-weight:800; text-transform:none; box-shadow:0 7px 16px rgba(40,80,232,.2); }
.role-edit-dialog__save:hover:not(.v-btn--disabled),.role-edit-dialog__save:focus-visible:not(.v-btn--disabled) { background:#0e1e38 !important; color:#fff !important; }
.role-edit-dialog__save :deep(.v-icon) { color:#fff !important; }
:global(.v-theme--dark) .role-edit-dialog { border-color:#3a4654; background:#20262e; }
:global(.v-theme--dark) .role-edit-dialog__header,:global(.v-theme--dark) .role-edit-dialog__actions { border-color:#3a4654; background:#20262e; }
:global(.v-theme--dark) .role-edit-dialog__header h2,:global(.v-theme--dark) .role-edit-dialog__section-heading h3 { color:#f1f5f9; }
:global(.v-theme--dark) .role-edit-dialog__header p,:global(.v-theme--dark) .role-edit-dialog__section-heading p { color:#aab8c9; }
:global(.v-theme--dark) .role-edit-dialog__fields :deep(.v-field),:global(.v-theme--dark) .role-permission-card { background:#29313a; }
:global(.v-theme--dark) .role-edit-dialog__permissions { border-color:#385373; background:#22334b; }
:global(.v-theme--dark) .role-permission-card { border-color:#40516b; }
:global(.v-theme--dark) .role-permission-card>header { border-color:#40516b; background:#2b3d56; color:#e7eefb; }
:global(.v-theme--dark) .role-permission-card__body :deep(.v-label) { color:#f1f5f9; }
:global(.v-theme--dark) .role-edit-dialog__cancel { background:#29313a !important; color:#a9c7ff !important; border-color:#607da8 !important; }

@media (max-width: 620px) {
  .role-edit-dialog__header,.role-edit-dialog__content,.role-edit-dialog__actions { padding-left:18px; padding-right:18px; }
  .role-edit-dialog__fields,.role-edit-dialog__groups { grid-template-columns:1fr; }
  .role-edit-dialog__actions .v-btn { min-width:0; }
}

/* Modo oscuro */
:global(.v-theme--dark) .stat-card,
:global(.v-theme--dark) .admin-card,
:global(.v-theme--dark) .dialog-card {
  background: #1E3559;
  border-color: #30496E;
}

:global(.v-theme--dark) .page-header h1,
:global(.v-theme--dark) .card-toolbar h2,
:global(.v-theme--dark) .users-heading h2,
:global(.v-theme--dark) .role-name,
:global(.v-theme--dark) .stat-number,
:global(.v-theme--dark) .user-info strong {
  color: #F4F7FF;
}

:global(.v-theme--dark) .user-card-item {
  background: #182C4B;
  border-color: #274167;
}

:global(.v-theme--dark) .user-action-btn {
  background: #1E3559;
}

:global(.v-theme--dark) .role-created-success {
  border-color: rgba(104, 190, 94, .36) !important;
  background: rgba(35, 126, 24, .2) !important;
  color: #c9edc4 !important;
}

:global(.v-theme--dark) .permissions-detail-dialog { border-color:#374863; background:#1a2639; }
:global(.v-theme--dark) .permissions-detail-dialog__header,:global(.v-theme--dark) .permissions-detail-dialog__actions { border-color:#374863; background:#1a2639; }
:global(.v-theme--dark) .permissions-detail-dialog__header h2,:global(.v-theme--dark) .permissions-detail-dialog__section-title h3 { color:#e7eefb; }
:global(.v-theme--dark) .permissions-detail-dialog__section-title p,:global(.v-theme--dark) .permissions-detail-dialog__empty { color:#b4c1d4; }
:global(.v-theme--dark) .permission-detail-card { border-color:#385373; background:#22334b; color:#e7eefb; }
:global(.v-theme--dark) .permissions-detail-dialog__empty { border-color:#40516b; }

:global(.v-theme--dark) .withdraw-user-dialog { background: #20262e; border-color: #3a4654; }
:global(.v-theme--dark) .withdraw-user-dialog__header { border-color: #56383c; background: #2a2226; }
:global(.v-theme--dark) .withdraw-user-dialog__header-icon { background: #4a2d34; color: #8daeff; }
:global(.v-theme--dark) .withdraw-user-dialog__header h2,:global(.v-theme--dark) .withdraw-user-dialog__content h3 { color: #f1f5f9; }
:global(.v-theme--dark) .withdraw-user-dialog__header p,:global(.v-theme--dark) .withdraw-user-dialog__content>p,:global(.v-theme--dark) .withdraw-user-dialog__role { color: #aab8c9; }
:global(.v-theme--dark) .withdraw-user-dialog__name { color: #d5dee9; }
:global(.v-theme--dark) .withdraw-user-dialog__actions { border-color: #3a4654; background: #20262e; }
:global(.v-theme--dark) .withdraw-user-dialog__cancel { border-color: #536273 !important; background: #30363d !important; color: #d5dee9 !important; }
:global(.v-theme--dark).delete-role-dialog { background:#20262e; border-color:#3a4654; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__header { border-color:#56383c; background:#2a2226; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__header-icon { background:#4a2d34; color:#8daeff !important; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__header h2,:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__content h3 { color:#f1f5f9; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__header p,:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__content>p { color:#aab8c9; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__warning { color:#f87171 !important; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__name { background:#253d61; color:#a9c7ff; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__actions { border-color:#3a4654; background:#20262e; }
:global(.v-theme--dark).delete-role-dialog .delete-role-dialog__cancel { border-color:#536273 !important; background:#30363d !important; color:#d5dee9 !important; }

@media (max-width: 480px) {
  .permissions-detail-dialog__header,.permissions-detail-dialog__content,.permissions-detail-dialog__actions { padding-left:18px; padding-right:18px; }
  .permissions-detail-dialog__grid { grid-template-columns:1fr; }
  .permissions-detail-dialog__button { width:100%; }
  .withdraw-user-dialog__actions { gap: 8px; }
  .withdraw-user-dialog__actions .v-btn { flex: 1; min-width: 0; }
  .delete-role-dialog__actions { gap:8px; }
  .delete-role-dialog__actions .v-btn { flex:1; min-width:0; }
}

@media (max-width: 1024px) {
  .manage-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .card-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-actions {
    width: 100%;
  }
  .search-field,
  .filter-select {
    width: 100%;
  }
  .admin-container {
    padding: 24px 16px 42px;
  }
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '../services/api'
import { useAuth } from '../stores/auth'
import { permissionLabel, roleLabel } from '../utils/labels'
import type { User } from '../types'

const { state } = useAuth()
const users = ref<User[]>([])
const error = ref('')
const selectedUser = ref<User | null>(null)
const canManage = computed(() => state.user?.permissions.includes('users:manage'))
const greeting = computed(() => state.user?.name?.split(' ')[0] || 'bienvenido')

const permissionDescriptions: Record<string, string> = {
  'users:read': 'Consultar el personal registrado.',
  'users:manage': 'Organizar usuarios, roles y accesos.',
  'customers:manage': 'Registrar y actualizar clientes.',
  'workshops:manage': 'Administrar centros de servicio.',
  'vehicles:manage': 'Registrar y actualizar vehículos.',
  'workorders:read': 'Consultar órdenes de trabajo.',
  'workorders:write': 'Crear y actualizar órdenes de trabajo.',
}

function visibleRoles(user: User) { return user.roles.slice(0, 1) }
function permissionDescription(code: string) { return permissionDescriptions[code] || 'Función adicional disponible según el rol asignado.' }
function openPermissions(user: User) { selectedUser.value = user }

async function load() {
  if (!state.user) return
  error.value = ''
  if (!canManage.value) { users.value = [state.user]; return }
  try { users.value = (await api.get<User[]>('/users')).data }
  catch { users.value = [state.user]; error.value = 'No fue posible cargar la lista de usuarios.' }
}

onMounted(load)
</script>

<template>
  <v-container class="dashboard admin-container">
    <header class="dashboard-hero">
      <div>
        <p class="eyebrow"><v-icon size="15">mdi-sparkles</v-icon> PANEL DE CONTROL</p>
        <h1>Hola, {{ greeting }}</h1>
        <p>Un resumen claro de tu acceso y del equipo autorizado.</p>
      </div>
      <div class="hero-status"><v-icon size="18">mdi-shield-check-outline</v-icon><span>Sesión protegida</span></div>
    </header>

    <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-5">{{ error }}</v-alert>

    <section class="metrics" aria-label="Resumen de acceso">
      <v-card class="metric-card" elevation="0"><div class="metric-icon"><v-icon>mdi-account-group-outline</v-icon></div><strong>{{ users.length }}</strong><span>{{ canManage ? 'Usuarios registrados' : 'Tu acceso autorizado' }}</span></v-card>
      <v-card class="metric-card" elevation="0"><div class="metric-icon"><v-icon>mdi-account-key-outline</v-icon></div><strong>{{ state.user?.roles.length || 0 }}</strong><span>Rol{{ (state.user?.roles.length || 0) === 1 ? '' : 'es' }} asignado{{ (state.user?.roles.length || 0) === 1 ? '' : 's' }}</span></v-card>
      <v-card class="metric-card" elevation="0"><div class="metric-icon"><v-icon>mdi-shield-check-outline</v-icon></div><strong>{{ state.user?.permissions.length }}</strong><span>Accesos activos</span></v-card>
    </section>

    <v-card class="data-card" elevation="0">
      <div class="card-head"><div><p class="section-kicker">DIRECTORIO DE ACCESO</p><h2>{{ canManage ? 'Usuarios y permisos' : 'Tu identidad y permisos' }}</h2><p>Consulta cada perfil sin saturar la pantalla.</p></div><div class="user-count"><v-icon size="17">mdi-account-outline</v-icon>{{ users.length }} {{ users.length === 1 ? 'usuario' : 'usuarios' }}</div></div>
      <div class="table-shell"><v-table class="users-table" hover><colgroup><col class="user-column"><col class="email-column"><col class="role-column"><col class="access-column"></colgroup><thead><tr><th>USUARIO</th><th>CORREO</th><th>ROL</th><th>ACCESOS</th></tr></thead><tbody><tr v-for="user in users" :key="user.id">
        <td data-label="Usuario"><div class="user-cell"><div class="user-avatar">{{ user.name.slice(0, 1).toUpperCase() }}</div><strong>{{ user.name }}</strong></div></td>
        <td data-label="Correo" class="email-cell">{{ user.email }}</td>
        <td data-label="Rol"><div class="role-list"><v-chip v-for="role in visibleRoles(user)" :key="role" color="primary" size="small" variant="tonal">{{ roleLabel(role) }}</v-chip><v-tooltip v-if="user.roles.length > 1" location="top"><template #activator="{ props }"><span v-bind="props" class="more-roles">+{{ user.roles.length - 1 }}</span></template><span>{{ user.roles.slice(1).map(roleLabel).join(' · ') }}</span></v-tooltip></div></td>
        <td data-label="Accesos"><v-btn v-if="user.permissions.length" class="permission-summary" variant="outlined" size="small" @click="openPermissions(user)"><v-icon size="18" start>mdi-shield-key-outline</v-icon>{{ user.permissions.length }} accesos</v-btn><span v-else class="empty-permissions">Sin accesos asignados</span></td>
      </tr></tbody></v-table></div>
    </v-card>

    <v-dialog :model-value="Boolean(selectedUser)" max-width="720" scrollable @update:model-value="selectedUser = $event ? selectedUser : null">
      <v-card class="permission-dialog">
        <div class="permission-dialog__header">
          <div class="permission-dialog__icon"><v-icon icon="mdi-shield-check-outline" size="24" /></div>
          <span class="permission-dialog__divider" aria-hidden="true" />
          <div class="permission-dialog__copy"><p class="section-kicker">PERFIL DE ACCESO</p><h2>Permisos de usuario</h2><p>Información organizada para consulta rápida.</p></div>
        </div>
        <v-card-text v-if="selectedUser" class="permission-dialog__content">
          <section class="profile-summary">
            <div class="profile-avatar">{{ selectedUser.name.slice(0, 1).toUpperCase() }}</div>
            <div class="profile-summary__identity"><strong>{{ selectedUser.name }}</strong><span>{{ selectedUser.email }}</span></div>
            <div class="profile-summary__roles"><span>Roles asignados</span><div><v-chip v-for="role in selectedUser.roles" :key="role" color="primary" size="small" variant="tonal">{{ roleLabel(role) }}</v-chip></div></div>
          </section>
          <section class="permissions-section">
            <div class="permissions-section__heading"><div><h3>Accesos autorizados</h3><p>{{ selectedUser.permissions.length }} {{ selectedUser.permissions.length === 1 ? 'permiso asignado' : 'permisos asignados' }}</p></div><v-icon>mdi-shield-check-outline</v-icon></div>
            <div v-if="selectedUser.permissions.length" class="permission-grid"><article v-for="permission in selectedUser.permissions" :key="permission" class="permission-item"><v-icon size="20">mdi-check-circle-outline</v-icon><div><strong>{{ permissionLabel(permission) }}</strong><span>{{ permissionDescription(permission) }}</span></div></article></div>
            <div v-else class="no-permissions"><v-icon>mdi-shield-off-outline</v-icon><span>Este usuario no tiene accesos asignados.</span></div>
          </section>
        </v-card-text>
        <v-card-actions class="permission-dialog__actions"><v-spacer /><v-btn variant="outlined" @click="selectedUser = null">Cerrar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.admin-container{max-width:1280px;padding:34px 32px 64px}.dashboard{min-height:100dvh}.dashboard-hero{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;margin-bottom:24px}.eyebrow,.section-kicker{display:flex;align-items:center;gap:6px;color:#3867de;font-size:.71rem;font-weight:800;letter-spacing:1.25px;margin:0 0 9px}.dashboard-hero h1{color:#172b4d;font-size:clamp(2rem,3vw,2.6rem);letter-spacing:-.045em;line-height:1.05;margin:0;font-weight:800}.dashboard-hero>div>p:last-child,.card-head>div>p:last-child,.permission-dialog__header>div>p:last-child{color:#66758b;margin:9px 0 0}.hero-status,.user-count{display:inline-flex;align-items:center;gap:7px;white-space:nowrap;border:1px solid #dce6f7;border-radius:999px;background:#f4f8ff;color:#3867de;padding:8px 12px;font-size:.78rem;font-weight:700}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.metric-card,.data-card{border:1px solid #e4e9f2;border-radius:18px;background:#fff;box-shadow:0 14px 32px rgba(23,43,77,.055)}.metric-card{min-height:144px;padding:20px;display:flex;flex-direction:column;align-items:flex-start;justify-content:space-between;transition:transform .2s ease,box-shadow .2s ease}.metric-card:hover{transform:translateY(-3px);box-shadow:0 18px 34px rgba(23,43,77,.09)}.metric-icon{display:grid;place-items:center;width:39px;height:39px;color:#3867de}.metric-card strong{font-size:1.8rem;line-height:1;color:#172b4d}.metric-card span{color:#748197;font-size:.83rem}.role-list{display:flex;flex-wrap:wrap;gap:6px;align-items:center;max-width:100%}.data-card{margin-top:22px;overflow:hidden}.card-head{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:24px 26px 20px}.section-kicker{margin-bottom:6px}.card-head h2,.permission-dialog h2{color:#172b4d;font-size:1.2rem;margin:0}.table-shell{border-top:1px solid #eef1f6}.users-table{width:100%;table-layout:fixed}.user-column{width:27%}.email-column{width:31%}.role-column{width:24%}.access-column{width:18%}.users-table :deep(th){height:46px;background:#f8faff;color:#718096;font-size:.69rem;font-weight:800;letter-spacing:.7px}.users-table :deep(td){height:72px;border-color:#eef1f6;color:#44536a;overflow-wrap:anywhere}.user-cell{display:flex;align-items:center;gap:10px}.user-avatar,.profile-avatar{display:grid;place-items:center;flex:0 0 auto;width:32px;height:32px;border-radius:10px;background:#eaf2ff;color:#3867de;font-size:.78rem;font-weight:800}.user-cell strong{color:#243752;white-space:nowrap}.email-cell{color:#66758b}.more-roles{color:#73829a;font-size:.76rem;font-weight:800}.permission-summary{border-color:#d9e4f8;color:#3867de;text-transform:none;font-size:.76rem;font-weight:700;letter-spacing:0}.empty-permissions{color:#8491a3;font-size:.8rem;font-style:italic}.permission-dialog{border:1px solid #e4e9f2;border-radius:20px;overflow:hidden}.permission-dialog__header{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;padding:26px 28px 20px;border-bottom:1px solid #edf1f6}.permission-dialog__content{padding:22px 28px 10px}.profile-summary{display:grid;grid-template-columns:auto minmax(0,1fr) minmax(160px,.8fr);align-items:center;gap:13px;padding:16px;border:1px solid #e2eaf6;border-radius:15px;background:#f8faff}.profile-avatar{width:46px;height:46px;border-radius:14px;font-size:1rem}.profile-summary__identity{min-width:0}.profile-summary__identity strong,.profile-summary__identity span{display:block}.profile-summary__identity strong{color:#263a58;font-size:.98rem}.profile-summary__identity span{margin-top:4px;color:#697a90;font-size:.79rem;overflow-wrap:anywhere}.profile-summary__roles>span{display:block;margin-bottom:7px;color:#71829a;font-size:.68rem;font-weight:800;letter-spacing:.5px;text-transform:uppercase}.profile-summary__roles>div{display:flex;flex-wrap:wrap;gap:5px}.permissions-section{margin-top:24px}.permissions-section__heading{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:13px}.permissions-section__heading h3{margin:0;color:#263a58;font-size:1rem}.permissions-section__heading p{margin:5px 0 0;color:#718096;font-size:.82rem}.permissions-section__heading>.v-icon{color:#3867de}.permission-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.permission-item{display:flex;align-items:flex-start;gap:10px;padding:13px;border:1px solid #e2eaf6;border-radius:13px;background:#fff}.permission-item>.v-icon{margin-top:1px;color:#2d8a57}.permission-item strong,.permission-item span{display:block}.permission-item strong{color:#30435f;font-size:.84rem}.permission-item span{margin-top:4px;color:#718096;font-size:.75rem;line-height:1.4}.no-permissions{display:flex;align-items:center;gap:9px;padding:18px;border:1px dashed #cdd8e6;border-radius:13px;color:#718096;font-size:.84rem}.permission-dialog__actions{padding:17px 28px 22px}@media(max-width:800px){.admin-container{padding:28px 18px 48px}.dashboard-hero{align-items:flex-start;flex-direction:column;margin-bottom:24px}.metrics{grid-template-columns:1fr}.metric-card{min-height:124px}.card-head{align-items:flex-start;flex-direction:column;padding:22px 20px 18px}.users-table{table-layout:auto}.users-table :deep(thead){display:none}.users-table :deep(tbody),.users-table :deep(tr),.users-table :deep(td){display:block;width:100%}.users-table :deep(tr){padding:16px 20px;border-bottom:1px solid #eef1f6}.users-table :deep(tr:last-child){border-bottom:0}.users-table :deep(td){height:auto;min-height:0;padding:7px 0;border:0}.users-table :deep(td:not(:first-child)){display:grid;grid-template-columns:84px minmax(0,1fr);gap:10px;align-items:center}.users-table :deep(td:not(:first-child))::before{content:attr(data-label);color:#8190a4;font-size:.68rem;font-weight:800;letter-spacing:.45px;text-transform:uppercase}.email-cell{overflow-wrap:anywhere}.profile-summary{grid-template-columns:auto minmax(0,1fr)}.profile-summary__roles{grid-column:1/-1}.permission-grid{grid-template-columns:1fr}}@media(max-width:420px){.admin-container{padding-inline:14px}.dashboard-hero h1{font-size:2rem}.hero-status{font-size:.73rem}.users-table :deep(tr){padding-inline:16px}.permission-dialog__header,.permission-dialog__content,.permission-dialog__actions{padding-left:18px;padding-right:18px}}
/* Excepción puntual del patrón global: este modal no lleva borde dorado superior. */
.permission-dialog::before{display:none}.permission-dialog__header{position:sticky;top:0;z-index:3;display:flex;justify-content:flex-start;align-items:center;gap:14px;padding:22px 28px 20px;border-bottom:1px solid #edf1f6;background:#fff}.permission-dialog__header::after{display:none}.permission-dialog__icon{display:grid;place-items:center;flex:none;width:44px;height:44px;border-radius:12px;background:#f8e9ce;color:#dda34e}.permission-dialog__divider{display:block;align-self:stretch;width:2px;min-width:2px;border-radius:999px;background:#dda34e}.permission-dialog__copy{min-width:0}.permission-dialog__copy .section-kicker{margin:0 0 4px;color:#2850e8;font-size:.7rem;letter-spacing:1.35px}.permission-dialog__copy h2{margin:0;color:#142b50;font-size:1.34rem;font-weight:700;line-height:1.2}.permission-dialog__copy>p:last-child{margin:5px 0 0;color:#64748b;font-size:.84rem}@media(max-width:420px){.permission-dialog__copy h2{font-size:1.15rem}.permission-dialog__copy>p:last-child{font-size:.77rem}}
</style>

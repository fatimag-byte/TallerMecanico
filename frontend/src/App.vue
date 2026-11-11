<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from './stores/auth'
import { authStorage, refreshSession } from './services/api'

const router = useRouter()
const route = useRoute()

const rail = ref(true)
const drawerOpen = ref(true)
const isCompact = ref(false)
const logoutDialog = ref(false)
const signingOut = ref(false)

const { logout, state } = useAuth()
const canManage = computed(() => state.user?.permissions.includes('users:manage'))
const showAdminLayout = computed(() => !route.meta.public)

window.addEventListener('auth-expired', () =>
  router.push({ path: '/login', query: { message: 'Tu sesión venció. Inicia sesión nuevamente.' } })
)

async function signOut() {
  signingOut.value = true
  try {
    await logout()
    logoutDialog.value = false
    router.push('/login')
  } finally {
    signingOut.value = false
  }
}

let renewalTimer: number | undefined

function syncLayout() {
  const compact = window.innerWidth <= 600
  if (compact !== isCompact.value) drawerOpen.value = !compact
  isCompact.value = compact
  if (!compact) drawerOpen.value = true
}

function toggleNavigation() {
  if (isCompact.value) drawerOpen.value = !drawerOpen.value
}

function expandNavigation() { if (!isCompact.value) rail.value = false }
function collapseNavigation() { if (!isCompact.value) rail.value = true }

onMounted(() => {
  localStorage.removeItem('taller-theme')
  syncLayout()
  window.addEventListener('resize', syncLayout)
  renewalTimer = window.setInterval(async () => {
    const expiry = Date.parse(localStorage.getItem('access_expires_at') || '')
    if (authStorage.refreshToken && Number.isFinite(expiry) && expiry - Date.now() < 60_000) {
      try {
        await refreshSession()
      } catch {
        authStorage.clear()
        router.push({ path: '/login', query: { message: 'Tu sesión venció. Inicia sesión nuevamente.' } })
      }
    }
  }, 30_000)
})

onUnmounted(() => {
  if (renewalTimer) window.clearInterval(renewalTimer)
  window.removeEventListener('resize', syncLayout)
})
</script>

<template>
  <v-app>
    <!-- Drawer lateral administrativo para /roles y /talleres -->
    <v-navigation-drawer
      v-if="showAdminLayout"
      v-model="drawerOpen"
      :permanent="!isCompact"
      :temporary="isCompact"
      :rail="!isCompact && rail"
      :width="236"
      :rail-width="76"
      color="#172B4D"
      class="admin-drawer"
      @mouseenter="expandNavigation"
      @mouseleave="collapseNavigation"
    >
      <div class="brand-mark" title="Taller Mecánico">
        <v-icon icon="mdi-tools" size="23" />
      </div>

      <v-list nav density="comfortable" class="mt-4">
        <v-tooltip location="right" text="Inicio">
          <template #activator="{ props }">
            <v-list-item
              v-bind="props"
              to="/dashboard"
              prepend-icon="mdi-view-dashboard-outline"
              title="Inicio"
            />
          </template>
        </v-tooltip>

        <v-tooltip location="right" text="Centro de servicio">
          <template #activator="{ props }">
            <v-list-item
              v-bind="props"
              to="/talleres"
              prepend-icon="mdi-storefront-outline"
              title="Centro de servicio"
            />
          </template>
        </v-tooltip>

        <v-tooltip location="right" text="Administrar talleres">
          <template #activator="{ props }"><v-list-item v-bind="props" to="/talleres/administracion" prepend-icon="mdi-storefront-check-outline" title="Administrar talleres" /></template>
        </v-tooltip>
        <v-tooltip location="right" text="Registrar cliente">
          <template #activator="{ props }"><v-list-item v-bind="props" to="/clientes/registro" prepend-icon="mdi-account-plus-outline" title="Registrar cliente" /></template>
        </v-tooltip>
        <v-tooltip location="right" text="Administrar clientes">
          <template #activator="{ props }"><v-list-item v-bind="props" to="/clientes" prepend-icon="mdi-account-group-outline" title="Administrar clientes" /></template>
        </v-tooltip>
        <v-tooltip location="right" text="Registrar vehículo">
          <template #activator="{ props }"><v-list-item v-bind="props" to="/vehiculos/registro" prepend-icon="mdi-car-info" title="Registrar vehículo" /></template>
        </v-tooltip>
        <v-tooltip location="right" text="Administrar vehículos">
          <template #activator="{ props }"><v-list-item v-bind="props" to="/vehiculos" prepend-icon="mdi-car-multiple" title="Administrar vehículos" /></template>
        </v-tooltip>

        <v-tooltip location="right" text="Administrar roles">
          <template #activator="{ props }">
            <v-list-item
              v-bind="props"
              to="/roles"
              prepend-icon="mdi-shield-account-outline"
              title="Administrar roles"
            />
          </template>
        </v-tooltip>

        <v-tooltip location="right" text="Registrar perfil">
          <template #activator="{ props }">
            <v-list-item
              v-bind="props"
              to="/roles/nuevo"
              prepend-icon="mdi-shield-plus-outline"
              title="Registrar perfil"
            />
          </template>
        </v-tooltip>
      </v-list>

      <template #append>
        <v-list nav density="comfortable" class="mb-3">
          <v-tooltip location="right" text="Cerrar sesión">
            <template #activator="{ props }">
              <v-list-item
                v-bind="props"
                prepend-icon="mdi-logout"
                title="Salir"
                @click="logoutDialog = true"
              />
            </template>
          </v-tooltip>
        </v-list>
      </template>
    </v-navigation-drawer>

    <!-- Barra superior para el entorno administrativo -->
    <v-app-bar v-if="showAdminLayout" elevation="0" class="admin-topbar">
      <v-btn
        icon="mdi-menu"
        variant="text"
        aria-label="Expandir o contraer menú"
        class="menu-toggle-btn mr-1"
        @click="toggleNavigation"
      />
      <v-app-bar-title class="admin-title">
        Administración del taller
      </v-app-bar-title>

      <v-spacer />

    </v-app-bar>

    <v-main :class="{ 'admin-main': showAdminLayout }">
      <router-view />
    </v-main>

    <v-dialog v-model="logoutDialog" max-width="430" :persistent="signingOut">
      <v-card class="logout-dialog">
        <header class="logout-dialog__header">
          <v-btn class="logout-dialog__close" icon="mdi-close" variant="text" aria-label="Cerrar confirmación" :disabled="signingOut" @click="logoutDialog = false" />
        </header>
        <v-card-text class="logout-dialog__content">
          <div class="logout-dialog__icon"><v-icon icon="mdi-logout" size="27" /></div>
          <h2>¿Cerrar sesión?</h2>
          <p>¿Estás seguro de que quieres cerrar tu sesión?</p>
        </v-card-text>
        <v-card-actions class="logout-dialog__actions">
          <v-btn class="logout-dialog__cancel" variant="outlined" :disabled="signingOut" @click="logoutDialog = false">Cancelar</v-btn>
          <v-btn class="logout-dialog__confirm" prepend-icon="mdi-logout" :loading="signingOut" :disabled="signingOut" @click="signOut">Cerrar sesión</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<style scoped>
.admin-drawer :deep(.v-navigation-drawer__content) {
  display: flex;
  flex-direction: column;
}

.brand-mark {
  width: 44px;
  height: 44px;
  margin: 16px auto 2px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  background: #D9A05B;
  color: #172B4D;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

.admin-drawer :deep(.v-list-item) {
  margin: 7px 10px;
  border-radius: 12px;
  color: #C3D6EA;
}

.admin-drawer :deep(.v-list-item--active) {
  background: #3867DE !important;
  color: #fff !important;
}

.admin-topbar {
  background: rgb(var(--v-theme-surface)) !important;
  border-bottom: 1px solid #E4E9F2;
  padding-inline: 8px;
}

.menu-toggle-btn {
  color: #172B4D;
}

.admin-title {
  color: #172B4D;
  font-size: 0.95rem;
  font-weight: 700;
}


.admin-main {
  background: #F6F8FC;
  min-height: 100dvh;
}

.logout-dialog { overflow:hidden; padding:0; border:1px solid #e3e9f1; border-radius:18px; background:#fff; box-shadow:0 20px 46px rgba(20,43,80,.18); }
.logout-dialog::before { display:none !important; }
.logout-dialog__header { display:flex; justify-content:flex-end; padding:13px 14px 0; }
.logout-dialog__icon { display:grid; width:54px; height:54px; place-items:center; margin:0 auto 15px; border-radius:50%; background:#fdebed; color:#dc3545; }
.logout-dialog__close { border-radius:9px; color:#64748b; }
.logout-dialog__close:hover:not(.v-btn--disabled) { background:#fdebed; color:#c64747; }
.logout-dialog__content { padding:7px 30px 25px; text-align:center; }
.logout-dialog__content h2 { margin:0; color:#172b4d; font-size:1.28rem; font-weight:800; }
.logout-dialog__content p { margin:9px 0 0; color:#64748b; font-size:.91rem; line-height:1.5; }
.logout-dialog__actions { justify-content:center; gap:11px; padding:17px 24px 24px; border-top:1px solid #edf0f4; }
.logout-dialog__cancel { min-width:138px; min-height:42px; border-color:#172b4d !important; background:#fff !important; color:#172b4d !important; font-weight:800; text-transform:none; }
.logout-dialog__cancel:hover:not(.v-btn--disabled),.logout-dialog__cancel:focus-visible:not(.v-btn--disabled) { border-color:#dda34e !important; background:#f8e9ce !important; color:#9a6419 !important; }
.logout-dialog__confirm { min-width:148px; min-height:42px; background:#dc3545 !important; color:#fff !important; font-weight:800; text-transform:none; box-shadow:0 7px 16px rgba(220,53,69,.22); }
.logout-dialog__confirm:hover:not(.v-btn--disabled),.logout-dialog__confirm:focus-visible:not(.v-btn--disabled) { background:#b91c2c !important; color:#fff !important; }
.logout-dialog__confirm :deep(.v-icon) { color:#fff !important; }


@media (max-width: 600px) {
  .admin-topbar {
    left: 0 !important;
  }
  .admin-main {
    padding-top: 0 !important;
  }
}
</style>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from './stores/auth'
import { authStorage, refreshSession } from './services/api'
const router = useRouter(); const { logout } = useAuth()
window.addEventListener('auth-expired', () => router.push({ path: '/login', query: { message: 'Tu sesión venció. Inicia sesión nuevamente.' } }))
async function signOut() { await logout(); router.push('/login') }
let renewalTimer: number | undefined
onMounted(() => {
  renewalTimer = window.setInterval(async () => {
    const expiry = Date.parse(localStorage.getItem('access_expires_at') || '')
    if (authStorage.refreshToken && Number.isFinite(expiry) && expiry - Date.now() < 60_000) {
      try { await refreshSession() } catch { authStorage.clear(); router.push({ path: '/login', query: { message: 'Tu sesión venció. Inicia sesión nuevamente.' } }) }
    }
  }, 30_000)
})
onUnmounted(() => { if (renewalTimer) window.clearInterval(renewalTimer) })
</script>
<template>
  <v-app><v-app-bar v-if="$route.path === '/dashboard'" color="primary" density="comfortable"><v-app-bar-title>Taller Mecánico</v-app-bar-title><v-btn prepend-icon="mdi-logout" @click="signOut">Salir</v-btn></v-app-bar><v-main><router-view /></v-main></v-app>
</template>

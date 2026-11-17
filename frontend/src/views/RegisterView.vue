<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import AuthForm from '../components/AuthForm.vue'
import AuthShell from '../components/AuthShell.vue'

const router = useRouter()
const { authenticate, state } = useAuth()
const error = ref('')
const success = ref('')
let successTimer: number | undefined

async function register(payload: { name?: string; paternal_surname?: string; maternal_surname?: string; phone?: string; email: string; password: string }) {
  error.value = ''
  success.value = ''
  try {
    await authenticate('register', { name: payload.name ?? '', paternal_surname: payload.paternal_surname ?? '', maternal_surname: payload.maternal_surname?.trim() || undefined, phone: payload.phone ?? '', email: payload.email, password: payload.password } as Record<string, string>)
    success.value = 'La cuenta ha sido creada correctamente.'
    if (successTimer) window.clearTimeout(successTimer)
    successTimer = window.setTimeout(() => { router.push('/dashboard') }, 3000)
  } catch (e: any) {
    const status = e.response?.status
    error.value = status === 409 ? 'Ya existe una cuenta asociada a este correo electrónico.' : status === 422 ? 'No se puede crear la cuenta. Revisa los datos proporcionados.' : status ? 'No se puede crear la cuenta. Inténtalo nuevamente.' : 'No se puede crear la cuenta. Verifica tu conexión e inténtalo nuevamente.'
  }
}

onBeforeUnmount(() => { if (successTimer) window.clearTimeout(successTimer) })
</script>
<template>
  <AuthShell wide eyebrow="COMIENZA AQUÍ" title="Crear cuenta" subtitle="Registra al personal que tendrá acceso al sistema de administración del taller. Los campos marcados con * son obligatorios.">
    <v-alert v-if="success" class="account-success-alert mb-5" variant="flat"><v-icon icon="mdi-check-circle" class="mr-2" />{{ success }}</v-alert>
    <v-alert v-if="error" class="account-error-alert mb-5" variant="flat" closable @click:close="error = ''"><v-icon icon="mdi-alert-circle" class="mr-2" />{{ error }}</v-alert>
    <AuthForm mode="register" :loading="state.loading" @submit="register" />
    <p class="text-center text-caption text-medium-emphasis mt-6">¿Ya tienes una cuenta? <router-link class="small-link" to="/login">Iniciar sesión</router-link></p>
  </AuthShell>
</template>
<style scoped>
.small-link { color:#3364a2;font-weight:700;text-decoration:none }.small-link:hover{color:#3867de;text-decoration:underline}
.account-success-alert{border:1px solid rgba(35,126,24,.2)!important;background:#eaf7ea!important;color:#237e18!important;font-weight:700}.account-success-alert :deep(.v-icon){color:#237e18!important}
.account-error-alert{border:1px solid rgba(198,40,40,.2)!important;background:#fdebec!important;color:#c62828!important;font-weight:700}.account-error-alert :deep(.v-icon){color:#c62828!important}
</style>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'
import AuthShell from '../components/AuthShell.vue'

const route = useRoute()
const router = useRouter()
const token = computed(() => String(route.query.token || ''))
const password = ref('')
const confirmation = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)

async function reset() {
  error.value = ''
  if (!token.value) { error.value = 'El enlace de recuperación es inválido o incompleto.'; return }
  if (password.value.length < 10) { error.value = 'La contraseña debe tener al menos 10 caracteres.'; return }
  if (password.value !== confirmation.value) { error.value = 'Las contraseñas no coinciden.'; return }
  loading.value = true
  try {
    await api.post('/auth/reset-password', { token: token.value, password: password.value })
    message.value = 'Contraseña actualizada. Ya puedes iniciar sesión.'
    setTimeout(() => router.push('/login'), 1200)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'No fue posible actualizar la contraseña.'
  } finally { loading.value = false }
}
</script>

<template>
  <AuthShell eyebrow="NUEVA CONTRASEÑA" title="Restablece el acceso" subtitle="Crea una contraseña segura para recuperar tu acceso.">
    <v-alert v-if="message" type="success" variant="tonal" class="mb-5">{{ message }}</v-alert>
    <v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{ error }}</v-alert>
    <v-form @submit.prevent="reset">
      <v-text-field v-model="password" label="Nueva contraseña" type="password" autocomplete="new-password" variant="outlined" hint="Mínimo 10 caracteres" persistent-hint />
      <v-text-field v-model="confirmation" label="Confirmar contraseña" type="password" autocomplete="new-password" variant="outlined" class="mt-2" />
      <v-btn type="submit" block color="primary" size="large" rounded="lg" class="text-none font-weight-bold mt-5" :loading="loading">Actualizar contraseña</v-btn>
    </v-form>
  </AuthShell>
</template>

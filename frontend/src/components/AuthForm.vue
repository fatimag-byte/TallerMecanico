<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
type RegisterPayload = { name: string; paternal_surname: string; maternal_surname: string; phone: string; email: string; password: string }
const props = defineProps<{ mode: 'login' | 'register'; loading: boolean }>()
const emit = defineEmits<{ submit: [payload: { email: string; password: string } | RegisterPayload] }>()
const form = reactive({ name: '', paternal_surname: '', maternal_surname: '', phone: '', email: '', password: '', confirmPassword: '' })
const visible = ref(false); const visibleConfirm = ref(false); const valid = ref(false)
const rules = {
  required: (value: string) => !!value?.trim() || 'Este campo es obligatorio.',
  person: (value: string) => /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+$/.test(value?.trim()) || 'Utiliza letras, espacios, apóstrofes o guiones.',
  optionalPerson: (value: string) => {
    const surname = value?.trim() ?? ''
    return !surname || /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+$/.test(surname) || 'El apellido materno solo puede contener letras, espacios, acentos, ñ, apóstrofes o guiones.'
  },
  email: (value: string) => /.+@.+\..+/.test(value) || 'Escribe un correo válido.',
  phone: (value: string) => { const digits = value.replace(/\D/g, '').replace(/^52/, ''); return digits.length === 10 || 'Ingresa un teléfono mexicano de 10 dígitos.' },
  password: (value: string) => (props.mode === 'login' || value.length >= 10) || 'La contraseña debe tener al menos 10 caracteres.',
  confirm: (value: string) => value === form.password || 'Las contraseñas no coinciden.'
}
const title = computed(() => {
  if (props.loading) return props.mode === 'login' ? 'Iniciando sesión...' : 'Creando cuenta...'
  return props.mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta'
})
function submit() { if (!valid.value) return; if (props.mode === 'login') emit('submit', { email: form.email, password: form.password }); else emit('submit', { name: form.name.trim(), paternal_surname: form.paternal_surname.trim(), maternal_surname: form.maternal_surname.trim(), phone: form.phone.trim(), email: form.email.trim(), password: form.password }) }
</script>
<template>
  <v-form v-model="valid" class="auth-form" @submit.prevent="submit">
    <template v-if="mode === 'register'"><div class="section-title"><span>01</span> Datos personales</div><div class="personal-grid"><div class="personal-field"><v-text-field v-model.trim="form.name" active label="Nombre *" placeholder="Ej. Fatima" prepend-inner-icon="mdi-account-outline" variant="outlined" color="primary" :rules="[rules.required, rules.person]" hint="Puedes ingresar uno o más nombres" persistent-hint hide-details="auto" /></div><div class="personal-field"><v-text-field v-model.trim="form.paternal_surname" active label="Apellido paterno *" placeholder="Ej. De Jesus" prepend-inner-icon="mdi-account-outline" variant="outlined" color="primary" :rules="[rules.required, rules.person]" hide-details="auto" /></div><div class="personal-field"><v-text-field v-model.trim="form.maternal_surname" active label="Apellido materno" placeholder="Ej. Granados" prepend-inner-icon="mdi-account-outline" variant="outlined" color="primary" :rules="[rules.optionalPerson]" hide-details="auto" /></div><div class="personal-field"><v-text-field v-model.trim="form.phone" active label="Teléfono *" placeholder="Ej. 5512345678" prepend-inner-icon="mdi-phone-outline" variant="outlined" color="primary" inputmode="tel" :rules="[rules.required, rules.phone]" hide-details="auto" /></div></div><div class="section-title mt-2"><span>02</span> Datos de acceso</div></template>
    <v-text-field v-model.trim="form.email" active label="Correo electrónico *" placeholder="correo@ejemplo.com" type="email" prepend-inner-icon="mdi-email-outline" variant="outlined" color="primary" :rules="[rules.required, rules.email]" hide-details="auto" />
    <v-text-field v-model="form.password" active label="Contraseña *" :type="visible ? 'text' : 'password'" prepend-inner-icon="mdi-lock-outline" :append-inner-icon="visible ? 'mdi-eye-off-outline' : 'mdi-eye-outline'" @click:append-inner="visible = !visible" variant="outlined" color="primary" :rules="[rules.required, rules.password]" :hint="mode === 'register' ? 'Mínimo 10 caracteres.' : undefined" persistent-hint hide-details="auto" />
    <v-text-field v-if="mode === 'register'" v-model="form.confirmPassword" active label="Confirmar contraseña *" :type="visibleConfirm ? 'text' : 'password'" prepend-inner-icon="mdi-lock-check-outline" :append-inner-icon="visibleConfirm ? 'mdi-eye-off-outline' : 'mdi-eye-outline'" @click:append-inner="visibleConfirm = !visibleConfirm" variant="outlined" color="primary" :rules="[rules.required, rules.confirm]" hide-details="auto" />
    <slot name="options" /><v-btn type="submit" block color="primary" size="large" rounded="lg" class="mt-5 text-none font-weight-bold action-btn" :loading="loading" :disabled="loading" :prepend-icon="mode === 'login' ? 'mdi-login' : 'mdi-account-plus-outline'">{{ title }}</v-btn>
  </v-form>
</template>
<style scoped>.auth-form :deep(.v-input){margin-bottom:16px}.auth-form :deep(.v-field){min-height:56px;border-radius:10px;background:#fff}.auth-form :deep(.v-field--focused){box-shadow:0 0 0 3px rgba(56,103,222,.14)}.auth-form :deep(.v-input--error .v-field){border-color:#c62828}.auth-form :deep(.v-input--error .v-field__outline__start),.auth-form :deep(.v-input--error .v-field__outline__notch::before),.auth-form :deep(.v-input--error .v-field__outline__notch::after),.auth-form :deep(.v-input--error .v-field__outline__end){border-color:#c62828!important}.auth-form :deep(.v-input--error .v-label){color:#c62828!important;opacity:1}.auth-form :deep(.v-input__details),.auth-form :deep(.v-messages){min-height:0}.auth-form :deep(.v-messages){padding-top:3px}.auth-form :deep(.v-input--error .v-messages__message){color:#c62828!important;font-size:.76rem;line-height:1.35;font-weight:400}.section-title{display:flex;align-items:center;gap:8px;color:#3364a2;font-weight:750;font-size:.83rem;padding-bottom:9px;margin-bottom:15px;border-bottom:1px solid #c3d6ea}.section-title span{color:#d9a05b}.personal-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:16px;row-gap:2px;align-items:start}.personal-field{min-width:0;align-self:start}.personal-field :deep(.v-input){margin-bottom:16px}.action-btn{min-height:48px;transition:transform .2s ease,background .2s ease,box-shadow .2s ease;box-shadow:0 9px 18px rgba(56,103,222,.2)}.action-btn:hover{background:#3364a2!important;transform:translateY(-2px);box-shadow:0 12px 24px rgba(51,100,162,.25)}@media(max-width:767px){.personal-grid{grid-template-columns:1fr;row-gap:0}}@media(prefers-reduced-motion:reduce){.action-btn{transition:none}.action-btn:hover{transform:none}}</style>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { activeWorkshops, createCustomer, findDuplicates } from '../services/customers'
import type { CustomerPayload, Workshop } from '../types'
import SmartAddressFields from '../components/SmartAddressFields.vue'

const workshops = ref<Workshop[]>([])
const saving = ref(false)
const notice = ref('')
const error = ref('')
const duplicateText = ref('')
const primaryEmailTouched = ref(false)
const secondaryEmailTouched = ref(false)
const primaryPhoneTouched = ref(false)
const secondaryPhoneTouched = ref(false)
const submitAttempted = ref(false)
const addressResetToken = ref(0)
const touched = ref<Record<string, boolean>>({ first_name: false, paternal_surname: false, street_and_number: false, workshop_id: false })
const form = ref<CustomerPayload & { workshop_id: number | null }>({
  workshop_id: null, first_name: '', paternal_surname: '', maternal_surname: '', street_and_number: '', neighborhood: '', postal_code: '', municipality: '', state: '', primary_email: '', secondary_email: '', primary_phone: '', secondary_phone: ''
})
const email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const gmailTypos = new Set(['gmal.com', 'gamil.com', 'gmial.com', 'gmail.co', 'gmail.con', 'gmail.comm', 'gmail.om', 'gmail,com'])
function emailMessage(value: string, required = false) {
  const normalized = value.trim().toLowerCase()
  if (!normalized) return required ? 'Ingresa un correo electrónico.' : ''
  if (!email.test(normalized)) return 'Escribe un correo electrónico válido.'
  const domain = normalized.split('@')[1]
  if (gmailTypos.has(domain) || (domain.startsWith('gmail') && domain !== 'gmail.com')) return 'Revisa el dominio: para Gmail usa @gmail.com.'
  return ''
}
const primaryEmailError = computed(() => emailMessage(form.value.primary_email, true))
const secondaryEmailError = computed(() => emailMessage(form.value.secondary_email ?? ''))
function phoneMessage(value: string, required = false) {
  if (!value.trim()) return required ? 'Ingresa un teléfono de 10 dígitos.' : ''
  return /^\d{10}$/.test(value) ? '' : 'El teléfono debe tener exactamente 10 dígitos.'
}
const primaryPhoneError = computed(() => phoneMessage(form.value.primary_phone, true))
const secondaryPhoneError = computed(() => phoneMessage(form.value.secondary_phone ?? ''))
function requiredMessage(value: string, label: string, minLength = 1) {
  if (!value.trim()) return `${label} es obligatorio.`
  return value.trim().length < minLength ? `${label} debe tener al menos ${minLength} caracteres.` : ''
}
const firstNameError = computed(() => requiredMessage(form.value.first_name, 'El nombre', 2))
const paternalSurnameError = computed(() => requiredMessage(form.value.paternal_surname, 'El apellido paterno', 2))
const streetError = computed(() => requiredMessage(form.value.street_and_number, 'La calle y número', 4))
const workshopError = computed(() => form.value.workshop_id ? '' : 'Selecciona un centro automotriz asociado.')
const stateError = computed(() => requiredMessage(form.value.state, 'El estado', 2))
const municipalityError = computed(() => requiredMessage(form.value.municipality, 'El municipio o alcaldía', 2))
const neighborhoodError = computed(() => requiredMessage(form.value.neighborhood, 'La colonia o localidad', 2))
const postalCodeError = computed(() => /^\d{5}$/.test(form.value.postal_code) ? '' : 'El código postal debe tener cinco dígitos.')
const addressValidation = computed(() => ({ state: stateError.value, municipality: municipalityError.value, neighborhood: neighborhoodError.value, postalCode: postalCodeError.value, force: submitAttempted.value }))
function displayError(message: string, field: string) { return submitAttempted.value || touched.value[field] ? message : '' }
function touch(field: string) { touched.value[field] = true }
const showPrimaryEmailError = computed(() => primaryEmailTouched.value || submitAttempted.value ? primaryEmailError.value : '')
const showSecondaryEmailError = computed(() => secondaryEmailTouched.value || submitAttempted.value ? secondaryEmailError.value : '')
const showPrimaryPhoneError = computed(() => primaryPhoneTouched.value || submitAttempted.value ? primaryPhoneError.value : '')
const showSecondaryPhoneError = computed(() => secondaryPhoneTouched.value || submitAttempted.value ? secondaryPhoneError.value : '')
const valid = computed(() => !firstNameError.value && !paternalSurnameError.value && !streetError.value && !workshopError.value && !stateError.value && !municipalityError.value && !neighborhoodError.value && !postalCodeError.value && !primaryEmailError.value && !secondaryEmailError.value && !primaryPhoneError.value && !secondaryPhoneError.value)
function resetForm() { form.value = { workshop_id: null, first_name: '', paternal_surname: '', maternal_surname: '', street_and_number: '', neighborhood: '', postal_code: '', municipality: '', state: '', primary_email: '', secondary_email: '', primary_phone: '', secondary_phone: '' }; primaryEmailTouched.value = false; secondaryEmailTouched.value = false; primaryPhoneTouched.value = false; secondaryPhoneTouched.value = false; touched.value = { first_name: false, paternal_surname: false, street_and_number: false, workshop_id: false }; submitAttempted.value = false; error.value = ''; duplicateText.value = ''; addressResetToken.value += 1 }
function payload(): CustomerPayload {
  const { workshop_id, ...customer } = form.value
  return { ...customer, maternal_surname: customer.maternal_surname || null, secondary_email: customer.secondary_email || null, secondary_phone: customer.secondary_phone ? customer.secondary_phone.replace(/\D/g, '') : null, primary_phone: customer.primary_phone.replace(/\D/g, '') }
}
async function review() {
  error.value = ''; duplicateText.value = ''; submitAttempted.value = true
  if (!valid.value || !form.value.workshop_id) { error.value = 'Completa los campos obligatorios con formatos válidos.'; return }
  saving.value = true
  try {
    const matches = await findDuplicates(form.value.workshop_id, payload())
    if (matches.contact_in_use || matches.exact.length) { error.value = 'El correo electrónico o teléfono ya está registrado. Verifica los datos antes de continuar.'; return }
    if (matches.possible.length) duplicateText.value = `Se detectaron ${matches.possible.length} coincidencia(s) por nombre. Puedes continuar si se trata de otra persona.`
    await createCustomer(form.value.workshop_id, payload())
    resetForm()
    notice.value = 'El cliente se registró correctamente.'
  } catch (cause: any) { error.value = cause.response?.data?.detail || (cause.response?.status === 409 ? 'El correo electrónico o teléfono ya está registrado. Verifica los datos antes de continuar.' : 'No fue posible completar el registro. Revisa los datos e inténtalo nuevamente.') }
  finally { saving.value = false }
}
onMounted(async () => { try { workshops.value = await activeWorkshops() } catch { error.value = 'No fue posible cargar los talleres activos.' } })
watch(error, value => { if (value) setTimeout(() => { if (error.value === value) error.value = '' }, 3000) })
watch(notice, value => { if (value) setTimeout(() => { if (notice.value === value) notice.value = '' }, 5000) })
</script>

<template>
  <v-container class="page-shell customer-register-page">
    <header class="page-header">
      <p class="eyebrow">GESTIÓN DE CLIENTES</p>
      <div class="header-row">
        <div class="header-icon"><v-icon icon="mdi-account-plus-outline" size="27" /></div>
        <div><h1>Registrar cliente</h1><p class="subtitle">Captura sus datos y asígnalo a un centro automotriz activo.</p></div>
      </div>
    </header>
    <v-alert v-if="notice" class="customer-register-success-alert mb-4" variant="flat"><v-icon icon="mdi-check-circle" class="mr-2" />{{ notice }}</v-alert>
    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error=''">{{ error }}</v-alert>
    <v-alert v-if="duplicateText" type="warning" variant="tonal" class="mb-4">{{ duplicateText }}</v-alert>
    <div class="register-grid">
      <div class="form-stack">
        <v-card class="module-card" elevation="0"><v-card-text>
          <div class="card-title"><div class="card-icon"><v-icon icon="mdi-account-outline" /></div><div><h2>Datos personales</h2><p>Los campos con * son obligatorios.</p></div></div><v-divider class="my-5" />
          <v-row><v-col cols="12" md="4"><v-text-field v-model.trim="form.first_name" label="Nombre *" placeholder="Ej. Andrea" prepend-inner-icon="mdi-account-outline" variant="outlined" density="comfortable" :error-messages="displayError(firstNameError, 'first_name')" @blur="touch('first_name')" /></v-col><v-col cols="12" md="4"><v-text-field v-model.trim="form.paternal_surname" label="Apellido paterno *" placeholder="Ej. Hernández" variant="outlined" density="comfortable" :error-messages="displayError(paternalSurnameError, 'paternal_surname')" @blur="touch('paternal_surname')" /></v-col><v-col cols="12" md="4"><v-text-field v-model.trim="form.maternal_surname" label="Apellido materno" placeholder="Ej. Salgado" variant="outlined" density="comfortable" /></v-col></v-row>
        </v-card-text></v-card>
        <v-card class="module-card" elevation="0"><v-card-text>
          <div class="card-title"><div class="card-icon"><v-icon icon="mdi-map-marker-outline" /></div><div><h2>Domicilio</h2><p>Información de contacto y ubicación del cliente.</p></div></div><v-divider class="my-5" />
          <v-row><v-col cols="12"><v-text-field v-model.trim="form.street_and_number" label="Calle y número *" placeholder="Ej. Avenida del Taller 120" prepend-inner-icon="mdi-road-variant" variant="outlined" density="comfortable" :error-messages="displayError(streetError, 'street_and_number')" @blur="touch('street_and_number')" /></v-col></v-row>
          <SmartAddressFields v-model:state="form.state" v-model:municipality="form.municipality" v-model:neighborhood="form.neighborhood" v-model:postal-code="form.postal_code" :validation="addressValidation" :reset-token="addressResetToken" />
        </v-card-text></v-card>
      </div>
      <div class="form-stack">
        <v-card class="module-card" elevation="0"><v-card-text>
          <div class="card-title"><div class="card-icon"><v-icon icon="mdi-storefront-outline" /></div><div><h2>Asociación</h2><p>El cliente se registra dentro de un taller activo.</p></div></div><v-divider class="my-5" />
          <v-select v-model="form.workshop_id" label="Centro automotriz asociado *" :items="workshops" item-title="name" item-value="id" :disabled="saving" prepend-inner-icon="mdi-storefront-outline" variant="outlined" density="comfortable" :error-messages="displayError(workshopError, 'workshop_id')" @blur="touch('workshop_id')" />
        </v-card-text></v-card>
        <v-card class="module-card" elevation="0"><v-card-text>
          <div class="card-title"><div class="card-icon"><v-icon icon="mdi-card-account-phone-outline" /></div><div><h2>Contacto</h2><p>Incluye al menos un correo y un teléfono principal.</p></div></div><v-divider class="my-5" />
          <v-row><v-col cols="12"><v-text-field v-model.trim="form.primary_email" label="Correo electrónico principal *" placeholder="cliente@correo.com" type="email" prepend-inner-icon="mdi-email-outline" variant="outlined" density="comfortable" :error-messages="showPrimaryEmailError" @blur="primaryEmailTouched=true" /></v-col><v-col cols="12"><v-text-field v-model.trim="form.secondary_email" label="Correo electrónico secundario" placeholder="alterno@correo.com" type="email" prepend-inner-icon="mdi-email-outline" variant="outlined" density="comfortable" :error-messages="showSecondaryEmailError" @blur="secondaryEmailTouched=true" /></v-col><v-col cols="12" md="6"><v-text-field v-model="form.primary_phone" label="Teléfono principal *" placeholder="10 dígitos" prepend-inner-icon="mdi-phone-outline" variant="outlined" density="comfortable" maxlength="10" inputmode="numeric" :error-messages="showPrimaryPhoneError" @blur="primaryPhoneTouched=true" /></v-col><v-col cols="12" md="6"><v-text-field v-model="form.secondary_phone" label="Teléfono secundario" placeholder="10 dígitos" prepend-inner-icon="mdi-phone-outline" variant="outlined" density="comfortable" maxlength="10" inputmode="numeric" :error-messages="showSecondaryPhoneError" @blur="secondaryPhoneTouched=true" /></v-col></v-row>
        </v-card-text></v-card>
      </div>
    </div>
    <footer class="action-footer"><p>Verificaremos los datos antes de completar el registro.</p><v-btn color="primary" size="large" prepend-icon="mdi-account-plus" :loading="saving" :disabled="saving" @click="review">Revisar y registrar</v-btn></footer>
  </v-container>
</template>
<style scoped>
.page-shell{max-width:1240px;padding:38px 32px 64px}.page-header{margin-bottom:28px}.header-row,.card-title{display:flex;gap:14px;align-items:flex-start}.header-icon,.card-icon{display:grid;place-items:center;flex:none;border-radius:12px}.header-icon{width:52px;height:52px;background:#edf3ff;color:#2850e8}.card-icon{width:42px;height:42px;background:#f8e9ce;color:#2850e8}.eyebrow{margin:0 0 8px;color:#3364a2;font-weight:800;letter-spacing:1.3px;font-size:.72rem}.page-header h1{margin:0;color:#172b4d;font-size:clamp(1.8rem,2.6vw,2.3rem);line-height:1.15;font-weight:800}.subtitle,.card-title p{margin:5px 0 0;color:#66758b;font-size:.88rem}.register-grid{display:grid;grid-template-columns:1.25fr 1fr;gap:24px}.form-stack{display:grid;gap:24px;align-content:start}.module-card,.action-footer{border:1px solid #e4e9f2;border-radius:16px;background:#fff;box-shadow:0 12px 28px rgba(23,43,77,.05)}.module-card{padding:6px}.card-title h2{margin:0;color:#172b4d;font-size:1.05rem}.action-footer{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 24px;margin-top:24px}.action-footer p{margin:0;color:#748197;font-size:.84rem}.action-footer .v-btn{text-transform:none;font-weight:700;border-radius:11px}.v-btn{text-transform:none}@media(max-width:900px){.register-grid{grid-template-columns:1fr}}@media(max-width:600px){.page-shell{padding:24px 16px 42px}.action-footer{align-items:stretch;flex-direction:column;text-align:center}}
:global(.v-theme--dark) .module-card,:global(.v-theme--dark) .action-footer{background:#1e3559;border-color:#30496e}:global(.v-theme--dark) .page-header h1,:global(.v-theme--dark) .card-title h2{color:#f4f7ff}:global(.v-theme--dark) .subtitle,:global(.v-theme--dark) .card-title p,:global(.v-theme--dark) .action-footer p{color:#c3d6ea}:global(.v-theme--dark) .customer-register-page .card-icon{background:#493b24;color:#8daeff}:global(.v-theme--dark) .customer-register-page .header-icon{background:#263a60;color:#8daeff}
.customer-register-success-alert{border:1px solid rgba(35,126,24,.2);background:#eaf7ea!important;color:#237e18!important;font-weight:700}.customer-register-success-alert :deep(.v-icon){color:#237e18!important}
</style>

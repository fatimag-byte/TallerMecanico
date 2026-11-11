<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Workshop } from '../types'
import { saveWorkshop } from '../services/workshops'
import SmartAddressFields from '../components/SmartAddressFields.vue'

const form = ref<Workshop>({
  name: '',
  rfc: '',
  contact_email: '',
  street_and_number: '',
  neighborhood: '',
  postal_code: '',
  state: '',
  municipality: '',
  photo_url: null,
  photo_name: null
})

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFileName = ref('No se eligió ningún archivo')
const photoError = ref('')
const saving = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const rfcRule = (value: string) => {
  if (!value) return 'El RFC es obligatorio.'
  const clean = value.trim().toUpperCase()
  if (clean.length < 12 || clean.length > 13) return 'Debe tener 12 o 13 caracteres.'
  if (!/^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$/.test(clean)) return 'Formato de RFC inválido.'
  return true
}

const emailRule = (value: string) => {
  if (!value) return 'El correo electrónico es obligatorio.'
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || 'Ingresa un correo electrónico válido.'
}

const postalCodeRule = (value: string) => {
  if (!value) return 'El código postal es obligatorio.'
  return /^\d{5}$/.test(value.trim()) || 'Debe contener exactamente 5 dígitos numéricos.'
}

const isFormValid = computed(() => {
  const f = form.value
  return (
    f.name.trim().length >= 3 &&
    rfcRule(f.rfc) === true &&
    emailRule(f.contact_email) === true &&
    f.street_and_number.trim().length >= 4 &&
    f.neighborhood.trim().length >= 3 &&
    postalCodeRule(f.postal_code) === true &&
    Boolean(f.state) &&
    Boolean(f.municipality) &&
    !photoError.value
  )
})

function handleRfcInput(event: Event) {
  const target = event.target as HTMLInputElement
  form.value.rfc = target.value.toUpperCase().replace(/[^A-Z0-9Ñ&]/g, '').slice(0, 13)
}

function triggerFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(event: Event) {
  photoError.value = ''
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const validTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!validTypes.includes(file.type)) {
    photoError.value = 'Formato no compatible. Usa JPG, PNG o WebP.'
    return
  }

  const maxSizeBytes = 15 * 1024 * 1024
  if (file.size > maxSizeBytes) {
    photoError.value = 'El archivo supera el tamaño máximo permitido de 15 MB.'
    return
  }

  selectedFileName.value = file.name
  form.value.photo_name = file.name

  const reader = new FileReader()
  reader.onload = (e) => {
    form.value.photo_url = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

function removePhoto() {
  form.value.photo_url = null
  form.value.photo_name = null
  selectedFileName.value = 'No se eligió ningún archivo'
  if (fileInput.value) fileInput.value.value = ''
}

async function submit() {
  if (!isFormValid.value) return
  saving.value = true
  errorMessage.value = ''

  try {
    const saved = await saveWorkshop({
      ...form.value,
      rfc: form.value.rfc.toUpperCase().trim(),
      postal_code: form.value.postal_code.trim()
    })
    form.value = { ...saved }
    successMessage.value = 'Centro automotriz registrado exitosamente.'
  } catch (cause: any) {
    errorMessage.value = cause.response?.data?.detail || 'No fue posible registrar el centro automotriz.'
  } finally {
    saving.value = false
  }
}

</script>

<template>
  <v-container class="admin-container workshop-page">
    <!-- Encabezado principal del módulo -->
    <header class="page-header">
      <p class="section-label">SUBSISTEMA • CONFIGURACIÓN OPERATIVA</p>
      <div class="header-main-row">
        <div class="header-icon-box">
          <v-icon icon="mdi-storefront-outline" size="28" />
        </div>
        <div>
          <h1>Alta de centro automotriz</h1>
          <p>Registra la información comercial, domicilio fiscal y presencia del centro de servicio automotriz.</p>
        </div>
      </div>
    </header>

    <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-5" closable @click:close="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>

    <v-form @submit.prevent="submit">
      <div class="workshop-grid">
        <!-- Columna Izquierda: Formulario de datos -->
        <div class="form-column">
          <!-- Card 1: Datos generales del establecimiento -->
          <v-card class="admin-card mb-6" elevation="0">
            <div class="card-heading">
              <div class="heading-icon blue">
                <v-icon icon="mdi-tools" />
              </div>
              <div>
                <h2>Datos del establecimiento</h2>
                <p>Todos los campos marcados con * son obligatorios.</p>
              </div>
            </div>

            <v-divider class="my-5" />

            <div class="form-fields">
              <div class="field-group">
                <label class="field-label">Nombre del centro automotriz *</label>
                <v-text-field
                  v-model.trim="form.name"
                  placeholder="Ej. Servicio Automotriz del Centro"
                  prepend-inner-icon="mdi-card-bulleted-outline"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || 'El nombre es obligatorio.', v => (v && v.length >= 3) || 'Mínimo 3 caracteres.']"
                  hide-details="auto"
                />
              </div>

              <div class="field-row">
                <div class="field-group">
                  <label class="field-label">RFC del establecimiento *</label>
                  <v-text-field
                    :model-value="form.rfc"
                    placeholder="Ej. ABC010203AB1"
                    prepend-inner-icon="mdi-card-account-details-outline"
                    variant="outlined"
                    density="comfortable"
                    single-line
                    maxlength="13"
                    :rules="[rfcRule]"
                    hide-details
                    @input="handleRfcInput"
                  />
                  <span class="field-help">12 o 13 caracteres. Se guardará en mayúsculas.</span>
                </div>

                <div class="field-group">
                  <label class="field-label">Correo electrónico de contacto *</label>
                  <v-text-field
                    v-model.trim="form.contact_email"
                    placeholder="contacto@centroautomotriz.com"
                    prepend-inner-icon="mdi-email-outline"
                    type="email"
                    variant="outlined"
                    density="comfortable"
                    single-line
                    :rules="[emailRule]"
                    hide-details
                  />
                  <span class="field-help" aria-hidden="true">&nbsp;</span>
                </div>
              </div>
            </div>
          </v-card>

          <!-- Card 2: Domicilio operativo -->
          <v-card class="admin-card" elevation="0">
            <div class="card-heading">
              <div class="heading-icon blue">
                <v-icon icon="mdi-map-marker-outline" />
              </div>
              <div>
                <h2>Domicilio del centro de servicio</h2>
                <p>Ubicación física donde se brindará la atención a vehículos y clientes.</p>
              </div>
            </div>

            <v-divider class="my-5" />

            <div class="form-fields">
              <div class="field-group">
                <label class="field-label">Calle y número *</label>
                <v-text-field
                  v-model.trim="form.street_and_number"
                  placeholder="Ej. Av. Reforma 125, Local 2"
                  prepend-inner-icon="mdi-road-variant"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || 'Calle y número son obligatorios.']"
                  hide-details="auto"
                />
                <span class="field-help">Incluye número exterior e interior, si corresponde.</span>
              </div>
              <SmartAddressFields
                v-model:state="form.state"
                v-model:municipality="form.municipality"
                v-model:neighborhood="form.neighborhood"
                v-model:postal-code="form.postal_code"
              />
            </div>
          </v-card>
        </div>

        <!-- Columna Derecha: Imagen / Fotografía -->
        <div class="photo-column">
          <v-card class="admin-card photo-card" elevation="0">
            <div class="card-heading">
              <div class="heading-icon blue">
                <v-icon icon="mdi-camera-outline" />
              </div>
              <div>
                <h2>Foto del centro automotriz</h2>
                <p>Una imagen para identificar el establecimiento.</p>
              </div>
            </div>

            <v-divider class="my-5" />

            <!-- Área de vista previa / carga -->
            <div class="photo-upload-zone" :class="{ 'has-photo': !!form.photo_url }" @click="triggerFilePicker">
              <template v-if="form.photo_url">
                <img :src="form.photo_url" alt="Fotografía del taller" class="photo-preview" />
                <div class="photo-overlay">
                  <v-btn size="small" color="white" variant="flat" prepend-icon="mdi-camera-retake-outline" @click.stop="triggerFilePicker">
                    Cambiar
                  </v-btn>
                  <v-btn size="small" color="error" variant="flat" prepend-icon="mdi-delete-outline" @click.stop="removePhoto">
                    Quitar
                  </v-btn>
                </div>
              </template>
              <template v-else>
                <div class="upload-placeholder">
                  <div class="placeholder-icon">
                    <v-icon icon="mdi-image-outline" size="38" />
                  </div>
                  <p class="placeholder-text">Agrega una foto de la fachada o del interior del taller.</p>
                </div>
              </template>
            </div>

            <!-- Selector de archivo estilizado -->
            <div class="file-picker-section mt-5">
              <label class="field-label">Seleccionar foto *</label>
              <div class="custom-file-row">
                <v-btn variant="outlined" class="choose-file-btn" @click="triggerFilePicker">
                  Elegir archivo
                </v-btn>
                <span class="file-chosen-label">{{ selectedFileName }}</span>
              </div>
              <input
                ref="fileInput"
                type="file"
                class="hidden-file-input"
                accept="image/jpeg,image/png,image/webp"
                @change="onFileSelected"
              />
              <span class="field-help mt-2 d-block">JPG, PNG o WebP. Máximo 15 MB.</span>
              <span v-if="photoError" class="photo-error-text">{{ photoError }}</span>
            </div>
          </v-card>
        </div>
      </div>

      <!-- Barra de acción inferior -->
      <footer class="action-footer mt-7">
        <p class="footer-note">Verifica que todos los campos obligatorios estén completos antes de registrar.</p>
        <v-btn
          type="submit"
          color="primary"
          size="large"
          prepend-icon="mdi-plus"
          class="submit-btn"
          :loading="saving"
          :disabled="!isFormValid || saving"
        >
          Registrar centro de servicio
        </v-btn>
      </footer>
    </v-form>

    <v-snackbar
      :model-value="!!successMessage"
      color="success"
      location="top"
      :timeout="4000"
      @update:model-value="val => { if (!val) successMessage = '' }"
    >
      <v-icon icon="mdi-check-circle-outline" class="mr-2" />{{ successMessage }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.admin-container {
  max-width: 1240px;
  padding: 38px 32px 64px;
}

.page-header {
  margin-bottom: 28px;
}

.section-label {
  margin: 0 0 8px;
  color: #3364A2;
  font-size: 0.72rem;
  letter-spacing: 1.4px;
  font-weight: 800;
}

.header-main-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-box {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: #EDF3FF;
  color: #3867DE;
  display: grid;
  place-items: center;
  flex: none;
  box-shadow: 0 6px 16px rgba(56, 103, 222, 0.12);
}

.page-header h1 {
  margin: 0;
  color: #172B4D;
  font-size: clamp(1.8rem, 2.6vw, 2.3rem);
  line-height: 1.15;
  letter-spacing: -0.6px;
  font-weight: 800;
}

.page-header p {
  margin: 6px 0 0;
  color: #66758B;
  font-size: 0.92rem;
}

.workshop-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1.15fr);
  gap: 24px;
  align-items: start;
}

.admin-card {
  border: 1px solid #E4E9F2;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(23, 43, 77, 0.05);
  padding: 28px;
}

.card-heading {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.card-heading h2 {
  margin: 0;
  color: #172B4D;
  font-size: 1.08rem;
  font-weight: 700;
}

.card-heading p {
  margin: 4px 0 0;
  color: #718096;
  font-size: 0.82rem;
}

.heading-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  flex: none;
}

.heading-icon.blue {
  background: #EDF3FF;
  color: #3867DE;
}

.workshop-page .heading-icon.blue {
  background: #F8E9CE;
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field-group {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.field-label {
  display: block;
  margin-bottom: 6px;
  color: #2D3E53;
  font-size: 0.82rem;
  font-weight: 700;
}

.field-help {
  display: block;
  margin-top: 5px;
  color: #7A8799;
  font-size: 0.74rem;
}

/* Zona de subida de imagen */
.photo-upload-zone {
  position: relative;
  height: 250px;
  border: 2px dashed #C3D6EA;
  border-radius: 14px;
  background: #F8FAFD;
  display: grid;
  place-items: center;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.2s ease;
}

.photo-upload-zone:hover {
  border-color: #3867DE;
  background: #F1F6FF;
}

.photo-upload-zone.has-photo {
  border-style: solid;
  border-color: #D3DFEE;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
}

.placeholder-icon {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  background: #EDF3FF;
  color: #3867DE;
  display: grid;
  place-items: center;
}

.placeholder-text {
  max-width: 260px;
  margin: 0;
  color: #718096;
  font-size: 0.84rem;
  line-height: 1.45;
}

.photo-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-overlay {
  position: absolute;
  inset: 0;
  background: rgba(23, 43, 77, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.photo-upload-zone:hover .photo-overlay {
  opacity: 1;
}

/* Custom file picker */
.hidden-file-input {
  display: none;
}

.custom-file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 10px;
  border: 1px solid #C3D6EA;
  border-radius: 10px;
  background: #FAFCFE;
}

.choose-file-btn {
  text-transform: none;
  font-weight: 700;
  border-radius: 8px;
  border-color: #C3D6EA;
  color: #172B4D;
  background: #fff;
}

.file-chosen-label {
  color: #69788D;
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-error-text {
  display: block;
  margin-top: 6px;
  color: #C62828;
  font-size: 0.76rem;
  font-weight: 600;
}

/* Barra inferior de acciones */
.action-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 28px;
  background: #fff;
  border: 1px solid #E4E9F2;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(23, 43, 77, 0.04);
}

.footer-note {
  margin: 0;
  color: #748197;
  font-size: 0.84rem;
}

.submit-btn {
  border-radius: 12px;
  text-transform: none;
  font-weight: 700;
  padding-inline: 26px;
  box-shadow: 0 8px 20px rgba(56, 103, 222, 0.24);
  letter-spacing: 0.2px;
}

/* Modo oscuro */
:global(.v-theme--dark) .admin-card,
:global(.v-theme--dark) .action-footer {
  background: #1E3559;
  border-color: #30496E;
}

:global(.v-theme--dark) .page-header h1,
:global(.v-theme--dark) .card-heading h2,
:global(.v-theme--dark) .field-label {
  color: #F4F7FF;
}

:global(.v-theme--dark) .page-header p,
:global(.v-theme--dark) .card-heading p,
:global(.v-theme--dark) .field-help,
:global(.v-theme--dark) .footer-note {
  color: #C3D6EA;
}

:global(.v-theme--dark) .photo-upload-zone {
  background: #142845;
  border-color: #385377;
}

:global(.v-theme--dark) .custom-file-row {
  background: #182C4B;
  border-color: #385377;
}

:global(.v-theme--dark) .file-chosen-label {
  color: #A9BFD8;
}

@media (max-width: 960px) {
  .workshop-grid {
    grid-template-columns: 1fr;
  }
  .action-footer {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }
}

@media (max-width: 600px) {
  .admin-container {
    padding: 24px 16px 42px;
  }
  .field-row {
    grid-template-columns: 1fr;
  }
  .admin-card {
    padding: 20px;
  }
}
</style>

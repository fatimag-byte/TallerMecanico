<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { activeWorkshops } from '../services/customers'
import { authStorage } from '../services/api'
import { deleteVehiclePhoto, getVehicle, listVehicles, setVehicleStatus, updateVehicle, uploadVehiclePhotos } from '../services/vehicles'
import type { Vehicle, VehicleUpdatePayload, Workshop } from '../types'

type VehicleEditForm = {
  make: string
  model: string
  year: number
  plate: string
  // Estos valores se conservan para no perder datos existentes, aunque ya no
  // forman parte de los controles editables del modal.
  version: string
  color: string
  mileage: number | null
}

const editableVehicleFields = ['make', 'model', 'year', 'plate'] as const

const list = ref<Vehicle[]>([])
const workshops = ref<Workshop[]>([])
const loading = ref(false)
const search = ref('')
const status = ref('todos')
const workshopId = ref<number | null>(null)
const details = ref<Vehicle | null>(null)
const confirmDisable = ref<Vehicle | null>(null)
const editing = ref<Vehicle | null>(null)
const editError = ref('')
const savingEdit = ref(false)
const editForm = reactive<VehicleEditForm>({ make: '', model: '', year: new Date().getFullYear(), plate: '', version: '', color: '', mileage: null })
const originalEdit = ref<VehicleEditForm | null>(null)
const pendingPhotos = ref<{ file: File; url: string }[]>([])
const deletedPhotoIds = ref<number[]>([])
const editPhotoInput = ref<HTMLInputElement | null>(null)
const replacingPhotoId = ref<number | null>(null)
const error = ref('')
const message = ref('')
const deactivationNotice = ref('')
const updateNotice = ref('')
const disabling = ref(false)
const isCompact = ref(window.innerWidth <= 900)
const activeCount = computed(() => list.value.filter(item => item.is_active).length)
const inactiveCount = computed(() => list.value.length - activeCount.value)
const canEdit = computed(() => {
  const roles = authStorage.user?.roles
  return Array.isArray(roles) && roles.some(role => ['administrador', 'recepcionista'].includes(role.toLowerCase()))
})
const editValid = computed(() => editForm.make.trim().length >= 2 && !!editForm.model.trim() && Number.isInteger(editForm.year) && editForm.year >= 1886 && editForm.year <= 2100 && !!editForm.plate.trim())
const editHasChanges = computed(() => {
  const original = originalEdit.value
  const fieldsChanged = !!original && editableVehicleFields.some(key => original[key] !== editForm[key])
  return fieldsChanged || pendingPhotos.value.length > 0 || deletedPhotoIds.value.length > 0
})
const remainingPhotos = computed(() => editing.value?.photos?.filter(photo => !deletedPhotoIds.value.includes(photo.id)) || [])

function formatDate(value?: string) { return value ? new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium' }).format(new Date(value)) : 'Sin fecha' }
function releasePhotos(vehicle: Vehicle | null) { vehicle?.photos?.forEach(photo => { if (photo.url?.startsWith('blob:')) URL.revokeObjectURL(photo.url) }) }
function clearPendingPhotos() { pendingPhotos.value.forEach(photo => URL.revokeObjectURL(photo.url)); pendingPhotos.value = []; deletedPhotoIds.value = []; replacingPhotoId.value = null; if (editPhotoInput.value) editPhotoInput.value.value = '' }
async function load() {
  loading.value = true; error.value = ''
  try { list.value = await listVehicles({ workshop_id: workshopId.value || undefined, search: search.value, status_filter: status.value }) }
  catch (cause: any) { error.value = cause.response?.data?.detail || 'No fue posible consultar los vehículos.' }
  finally { loading.value = false }
}
async function openDetails(item: Vehicle) {
  error.value = ''
  try { releasePhotos(details.value); details.value = await getVehicle(item.id) }
  catch (cause: any) { error.value = cause.response?.data?.detail || 'No fue posible consultar la ficha del vehículo.' }
}
function closeDetails() { releasePhotos(details.value); details.value = null }
async function openEdit(item: Vehicle) {
  editError.value = ''; error.value = ''
  try {
    releasePhotos(editing.value)
    const vehicle = await getVehicle(item.id)
    editing.value = vehicle
    const values: VehicleEditForm = {
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year,
      plate: vehicle.plate || '',
      version: vehicle.version || '',
      color: vehicle.color || '',
      mileage: vehicle.mileage ?? null,
    }
    Object.assign(editForm, values)
    originalEdit.value = { ...values }
    clearPendingPhotos()
  } catch (cause: any) { error.value = cause.response?.data?.detail || 'No fue posible cargar el vehículo para editar.' }
}
function closeEdit() { clearPendingPhotos(); releasePhotos(editing.value); editing.value = null; originalEdit.value = null; editError.value = '' }
function openPhotoPicker() { if (!savingEdit.value) { replacingPhotoId.value = null; editPhotoInput.value?.click() } }
function replacePhoto(photoId: number) { if (!savingEdit.value) { replacingPhotoId.value = photoId; editPhotoInput.value?.click() } }
function addPhotos(event: Event) {
  const files = Array.from((event.target as HTMLInputElement).files || [])
  const invalid = files.find(file => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 15 * 1024 * 1024)
  if (invalid) { editError.value = 'Cada fotografía debe ser JPG, PNG o WebP y pesar como máximo 15 MB.'; if (editPhotoInput.value) editPhotoInput.value.value = ''; return }
  if (replacingPhotoId.value !== null) markPhotoForRemoval(replacingPhotoId.value)
  pendingPhotos.value = [...pendingPhotos.value, ...files.map(file => ({ file, url: URL.createObjectURL(file) }))]
  replacingPhotoId.value = null
  if (editPhotoInput.value) editPhotoInput.value.value = ''
}
function markPhotoForRemoval(photoId: number) { if (!savingEdit.value && !deletedPhotoIds.value.includes(photoId)) deletedPhotoIds.value = [...deletedPhotoIds.value, photoId] }
function removePendingPhoto(index: number) { const [photo] = pendingPhotos.value.splice(index, 1); if (photo) URL.revokeObjectURL(photo.url) }
async function saveEdit() {
  if (!editing.value || !editValid.value || !editHasChanges.value) return
  savingEdit.value = true; editError.value = ''
  try {
    const payloadChanged = !!originalEdit.value && editableVehicleFields.some(key => originalEdit.value?.[key] !== editForm[key])
    if (payloadChanged) {
      const payload: VehicleUpdatePayload = {
        make: editForm.make.trim(),
        model: editForm.model.trim(),
        year: editForm.year,
        plate: editForm.plate.trim(),
      }
      await updateVehicle(editing.value.id, payload)
    }
    for (const photoId of deletedPhotoIds.value) await deleteVehiclePhoto(editing.value.id, photoId)
    if (pendingPhotos.value.length) await uploadVehiclePhotos(editing.value.id, pendingPhotos.value.map(photo => photo.file))
    await load()
    updateNotice.value = 'Los datos se actualizaron correctamente.'
    closeEdit()
  } catch (cause: unknown) {
    console.error('Vehicle update failed', cause)
    editError.value = 'No fue posible actualizar la información.'
  }
  finally { savingEdit.value = false }
}
async function disable() {
  if (!confirmDisable.value) return
  disabling.value = true
  try { await setVehicleStatus(confirmDisable.value.id, false); confirmDisable.value = null; await load(); deactivationNotice.value = 'El vehículo se dio de baja correctamente.' }
  catch (cause: any) { error.value = cause.response?.data?.detail || 'No fue posible desactivar el vehículo.' }
  finally { disabling.value = false }
}
watch([search, status, workshopId], load)
watch(error, value => { if (value) setTimeout(() => { if (error.value === value) error.value = '' }, 5000) })
watch(deactivationNotice, value => { if (value) setTimeout(() => { if (deactivationNotice.value === value) deactivationNotice.value = '' }, 5000) })
watch(editError, value => { if (value) setTimeout(() => { if (editError.value === value) editError.value = '' }, 3000) })
watch(updateNotice, value => { if (value) setTimeout(() => { if (updateNotice.value === value) updateNotice.value = '' }, 3000) })
onMounted(async () => {
  window.addEventListener('resize', () => { isCompact.value = window.innerWidth <= 900 })
  try { workshops.value = await activeWorkshops() } catch { error.value = 'No fue posible cargar los talleres disponibles.' }
  await load()
})
</script>

<template>
  <v-container class="page-shell vehicles-admin">
    <header class="page-header"><p class="eyebrow">VEHÍCULOS</p><div class="header-row"><div class="header-icon"><v-icon icon="mdi-car-multiple" size="27" /></div><div><h1>Administración de vehículos</h1><p class="subtitle">Consulta unidades, su propietario y su historial visual.</p></div></div></header>
    <v-alert v-if="updateNotice" class="vehicle-update-success mb-5" variant="flat"><v-icon icon="mdi-check-circle" class="mr-2" />{{ updateNotice }}</v-alert><v-alert v-if="deactivationNotice" class="vehicle-deactivation-success mb-5" variant="flat"><v-icon icon="mdi-check-circle" class="mr-2" />{{ deactivationNotice }}</v-alert><v-alert v-if="error" type="error" variant="tonal" closable class="mb-5" @click:close="error=''">{{ error }}</v-alert>
    <section class="metrics"><v-card class="metric" elevation="0"><div class="metric-icon blue"><v-icon icon="mdi-car-multiple" /></div><strong>{{ list.length }}</strong><span>Vehículos registrados</span></v-card><v-card class="metric" elevation="0"><div class="metric-icon green"><v-icon icon="mdi-check-circle-outline" /></div><strong>{{ activeCount }}</strong><span>Vehículos activos</span></v-card><v-card class="metric" elevation="0"><div class="metric-icon amber"><v-icon icon="mdi-car-off" /></div><strong>{{ inactiveCount }}</strong><span>Vehículos inactivos</span></v-card></section>
    <v-card class="module-card" elevation="0">
      <div class="table-heading"><div><h2>Unidades registradas</h2><p>Busca por VIN, placas, marca, modelo o propietario.</p></div></div><v-divider />
      <v-card-text class="filter-row"><v-text-field v-model="search" label="Buscar vehículo" prepend-inner-icon="mdi-magnify" variant="outlined" density="comfortable" hide-details clearable /><v-select v-model="status" label="Estado" :items="[{title:'Todos los estados',value:'todos'},{title:'Activos',value:'activos'},{title:'Inactivos',value:'inactivos'}]" variant="outlined" density="comfortable" hide-details /><v-select v-model="workshopId" clearable label="Centro automotriz" :items="workshops" item-title="name" item-value="id" variant="outlined" density="comfortable" hide-details /></v-card-text>
      <div v-if="!isCompact" class="desktop-table"><v-table class="vehicle-table" hover><thead><tr><th>Vehículo</th><th>Propietario</th><th>Centro automotriz</th><th>Fotos</th><th>Estado</th><th class="text-right">Acciones</th></tr></thead><tbody><tr v-if="loading"><td colspan="6" class="empty-row"><v-progress-circular indeterminate color="primary" size="24" /> Cargando vehículos…</td></tr><tr v-else-if="!list.length"><td colspan="6" class="empty-row"><v-icon icon="mdi-car-off" size="26" /> No se encontraron vehículos con esos filtros.</td></tr><tr v-for="item in list" :key="item.id"><td><div class="vehicle-cell"><div class="mini-car"><v-icon icon="mdi-car" /></div><div><strong>{{ item.make }} {{ item.model }}</strong><span>{{ item.year }} · {{ item.plate || 'Sin placas' }}</span><small>{{ item.vin }}</small></div></div></td><td><div class="person-cell"><v-avatar size="34" color="primary" variant="tonal">{{ item.customer_name?.charAt(0) || 'C' }}</v-avatar><span>{{ item.customer_name }}</span></div></td><td><div class="workshop-cell"><v-icon icon="mdi-storefront-outline" size="17" /><span>{{ item.workshop_name }}</span></div></td><td><v-chip size="small" variant="tonal" color="primary"><v-icon start size="15" icon="mdi-image-multiple-outline" />{{ item.photo_count }} {{ item.photo_count === 1 ? 'foto' : 'fotos' }}</v-chip></td><td><v-chip :color="item.is_active ? 'success' : 'grey'" size="small" variant="tonal"><v-icon start size="14" :icon="item.is_active ? 'mdi-check-circle' : 'mdi-pause-circle'" />{{ item.is_active ? 'Activo' : 'Inactivo' }}</v-chip></td><td><div class="actions"><v-btn :aria-label="`Ver ficha de ${item.make} ${item.model}`" icon="mdi-eye-outline" size="small" color="primary" variant="tonal" @click="openDetails(item)" /><v-btn v-if="canEdit" :aria-label="`Editar ${item.make} ${item.model}`" icon="mdi-pencil-outline" size="small" color="primary" variant="tonal" @click="openEdit(item)" /><v-btn :aria-label="`Desactivar ${item.make} ${item.model}`" icon="mdi-car-off" size="small" color="error" variant="tonal" :disabled="!item.is_active" @click="confirmDisable=item" /></div></td></tr></tbody></v-table></div>
      <div v-else class="mobile-list"><div v-if="loading" class="empty-row"><v-progress-circular indeterminate color="primary" size="24" /> Cargando vehículos…</div><div v-else-if="!list.length" class="empty-row"><v-icon icon="mdi-car-off" size="26" /> No se encontraron vehículos con esos filtros.</div><v-card v-for="item in list" :key="item.id" class="vehicle-mobile" elevation="0"><div class="vehicle-mobile__top"><div class="mini-car"><v-icon icon="mdi-car" /></div><div class="grow"><strong>{{ item.make }} {{ item.model }}</strong><span>{{ item.year }} · {{ item.plate || 'Sin placas' }}</span></div><v-chip :color="item.is_active ? 'success' : 'grey'" size="x-small" variant="tonal">{{ item.is_active ? 'Activo' : 'Inactivo' }}</v-chip></div><p><v-icon icon="mdi-barcode" /> {{ item.vin }}</p><p><v-icon icon="mdi-account-outline" /> {{ item.customer_name }}</p><p><v-icon icon="mdi-storefront-outline" /> {{ item.workshop_name }}</p><div class="mobile-actions"><v-chip size="small" variant="tonal" color="primary"><v-icon start size="15" icon="mdi-image-multiple-outline" />{{ item.photo_count }}</v-chip><v-spacer /><v-btn :aria-label="`Ver ficha de ${item.make} ${item.model}`" icon="mdi-eye-outline" size="small" color="primary" variant="tonal" @click="openDetails(item)" /><v-btn v-if="canEdit" :aria-label="`Editar ${item.make} ${item.model}`" icon="mdi-pencil-outline" size="small" color="primary" variant="tonal" @click="openEdit(item)" /><v-btn :aria-label="`Desactivar ${item.make} ${item.model}`" icon="mdi-car-off" size="small" color="error" variant="tonal" :disabled="!item.is_active" @click="confirmDisable=item" /></div></v-card></div>
    </v-card>
    <v-dialog :model-value="!!details" max-width="960" persistent class="vehicle-details-dialog"><v-card class="dialog-card vehicle-details"><header class="vehicle-details__header"><div class="vehicle-details__icon"><v-icon icon="mdi-car-info" size="29" /></div><span class="vehicle-details__divider" aria-hidden="true" /><div class="grow"><p class="vehicle-details__eyebrow">FICHA DEL VEHÍCULO</p><h2>{{ details?.make }} {{ details?.model }}</h2><p class="vehicle-details__vin"><v-icon icon="mdi-barcode" size="17" />{{ details?.vin }}</p></div><v-btn class="vehicle-details__close" aria-label="Cerrar ficha" icon="mdi-close" variant="text" @click="closeDetails" /></header><v-card-text class="vehicle-details__content"><section class="vehicle-details__section"><div class="vehicle-details__section-heading"><div class="vehicle-details__section-icon"><v-icon icon="mdi-account-outline" size="21" /></div><div><h3>Propietario</h3><p>Información de contacto del cliente asociado.</p></div></div><article class="vehicle-owner-card"><v-avatar class="vehicle-owner-card__avatar" size="54">{{ details?.owner?.name?.charAt(0) || details?.customer_name?.charAt(0) || 'C' }}</v-avatar><div class="grow"><strong>{{ details?.owner?.name || details?.customer_name }}</strong><span>{{ details?.owner?.primary_phone || 'Sin teléfono registrado' }}</span></div><div class="vehicle-owner-card__contact"><span><v-icon icon="mdi-email-outline" size="18" />{{ details?.owner?.primary_email || 'Sin correo registrado' }}</span><span v-if="details?.owner?.secondary_email"><v-icon icon="mdi-email-plus-outline" size="17" />{{ details.owner.secondary_email }}</span></div></article><p class="vehicle-owner-address"><v-icon icon="mdi-map-marker-outline" size="19" />{{ details?.owner?.address || 'Domicilio no registrado' }}</p></section><section class="vehicle-details__section"><div class="vehicle-details__section-heading"><div class="vehicle-details__section-icon"><v-icon icon="mdi-car-outline" size="21" /></div><div><h3>Datos del vehículo</h3><p>Información técnica y administrativa de la unidad.</p></div></div><div class="vehicle-details__spec-grid"><article><span>Marca</span><strong>{{ details?.make }}</strong></article><article><span>Modelo</span><strong>{{ details?.model }}</strong></article><article><span>Año</span><strong>{{ details?.year }}</strong></article><article><span>Placas</span><strong>{{ details?.plate || 'Sin registro' }}</strong></article></div></section><section class="vehicle-details__section"><div class="vehicle-details__section-heading"><div class="vehicle-details__section-icon"><v-icon icon="mdi-image-multiple-outline" size="21" /></div><div><h3>Fotografías del vehículo</h3><p>{{ details?.photos?.length || 0 }} archivo(s) asociado(s) a esta unidad.</p></div></div><div v-if="details?.photos?.length" class="vehicle-details__photo-grid"><v-img v-for="photo in details.photos" :key="photo.id" :src="photo.url" :alt="`Fotografía de ${details.make} ${details.model}`" height="170" cover class="vehicle-details__photo"><template #placeholder><div class="photo-placeholder"><v-progress-circular indeterminate color="primary" /></div></template></v-img></div><div v-else class="vehicle-details__empty-photos"><v-icon icon="mdi-image-off-outline" size="28" /><span>Este vehículo aún no tiene fotografías registradas.</span></div></section></v-card-text><v-card-actions class="vehicle-details__actions"><v-spacer /><v-btn class="vehicle-details__close-button" variant="outlined" prepend-icon="mdi-close" @click="closeDetails">Cerrar ficha</v-btn></v-card-actions></v-card></v-dialog>
    <v-dialog :model-value="!!editing" max-width="840" persistent class="vehicle-edit-dialog" content-class="vehicle-edit-overlay-content">
      <v-card class="dialog-card vehicle-edit">
        <header class="vehicle-edit__header">
          <div class="edit-header-icon"><v-icon icon="mdi-pencil-outline" size="24" /></div>
          <div class="vehicle-edit__heading"><h2>Actualizar vehículo</h2><p>Modifica los datos principales sin cambiar la asociación existente.</p></div>
          <v-spacer />
          <v-btn class="edit-close-button" aria-label="Cerrar actualización" icon="mdi-close" variant="text" :disabled="savingEdit" @click="closeEdit" />
        </header>
        <v-alert v-if="editError" style="margin:14px 28px 0" type="error" variant="tonal"><v-icon icon="mdi-alert-circle-outline" class="mr-2" />{{ editError }}</v-alert>
        <v-card-text class="edit-content">
          <section class="linked-info" aria-labelledby="linked-info-title">
            <div class="edit-section-heading"><div class="section-heading__icon"><v-icon icon="mdi-link-variant" size="20" /></div><h3 id="linked-info-title">Información vinculada</h3></div>
            <div class="readonly-association">
              <article class="association-card"><v-icon icon="mdi-account-outline" size="21" /><div><span>Cliente asociado</span><strong>{{ editing?.customer_name }}</strong></div></article>
              <article class="association-card"><v-icon icon="mdi-storefront-outline" size="21" /><div><span>Centro automotriz</span><strong>{{ editing?.workshop_name }}</strong></div></article>
            </div>
            <div class="vin-panel"><v-icon icon="mdi-barcode" size="22" /><div class="vin-panel__value"><span>Número de serie (VIN)</span><strong>{{ editing?.vin }}</strong></div><v-chip class="vin-lock" size="small" variant="flat"><v-icon start icon="mdi-lock-outline" size="14" />No modificable</v-chip></div>
            <p class="vin-note"><v-icon icon="mdi-information-outline" size="16" />El VIN es permanente y no se puede modificar.</p>
          </section>
          <section class="vehicle-data" aria-labelledby="vehicle-data-title">
            <div class="edit-section-heading edit-section-heading--data"><div class="section-heading__title"><div class="section-heading__icon"><v-icon icon="mdi-square-edit-outline" size="20" /></div><h3 id="vehicle-data-title">Datos del vehículo</h3></div><v-chip class="required-chip" size="small" variant="flat">Campos obligatorios *</v-chip></div>
            <v-row class="edit-fields">
              <v-col cols="12" md="6"><v-text-field v-model.trim="editForm.make" label="Marca *" variant="outlined" density="comfortable" /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model.trim="editForm.model" label="Modelo *" variant="outlined" density="comfortable" /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model.number="editForm.year" label="Año *" type="number" :min="1886" :max="2100" variant="outlined" density="comfortable" /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model.trim="editForm.plate" label="Placas *" maxlength="12" variant="outlined" density="comfortable" /></v-col>
            </v-row>
          </section>
          <section class="edit-photos">
            <div class="edit-section-heading"><div class="section-heading__icon"><v-icon icon="mdi-image-multiple-outline" size="20" /></div><div><h3>Fotografías del vehículo</h3><p>{{ remainingPhotos.length + pendingPhotos.length ? `${remainingPhotos.length + pendingPhotos.length} archivo(s) que se guardarán para esta unidad.` : 'No hay fotografías registradas.' }}</p></div></div>
            <input ref="editPhotoInput" class="sr-only" type="file" accept="image/jpeg,image/png,image/webp" multiple @change="addPhotos" />
            <div class="vehicle-photo-cards">
              <article v-for="(photo, index) in remainingPhotos" :key="photo.id" class="vehicle-photo-card">
                <v-img :src="photo.url" :alt="`Fotografía de ${editing?.make} ${editing?.model}`" height="154" cover class="vehicle-photo" />
                <span v-if="index === 0" class="photo-principal"><v-icon icon="mdi-star" size="14" />Principal</span>
                <div class="vehicle-photo-card__actions"><v-btn :aria-label="`Reemplazar fotografía ${index + 1}`" icon="mdi-pencil-outline" size="small" @click="replacePhoto(photo.id)" /><v-btn :aria-label="`Eliminar fotografía ${index + 1}`" icon="mdi-delete-outline" size="small" @click="markPhotoForRemoval(photo.id)" /></div>
              </article>
              <article v-for="(photo, index) in pendingPhotos" :key="photo.url" class="vehicle-photo-card">
                <v-img :src="photo.url" :alt="photo.file.name" height="154" cover class="vehicle-photo" />
                <span v-if="remainingPhotos.length === 0 && index === 0" class="photo-principal"><v-icon icon="mdi-star" size="14" />Principal</span>
                <div class="vehicle-photo-card__actions"><v-btn :aria-label="`Agregar otra fotografía desde ${photo.file.name}`" icon="mdi-plus" size="small" @click="openPhotoPicker" /><v-btn :aria-label="`Eliminar ${photo.file.name}`" icon="mdi-delete-outline" size="small" @click="removePendingPhoto(index)" /></div>
              </article>
              <button class="add-photo-card" type="button" @click="openPhotoPicker"><v-icon icon="mdi-image-plus-outline" size="29" /><span>Agregar fotografías</span><small>JPG, PNG o WebP · máximo 15 MB</small></button>
            </div>
          </section>
        </v-card-text>
        <v-card-actions class="dialog-actions edit-actions"><v-spacer /><v-btn class="edit-cancel-button" variant="outlined" prepend-icon="mdi-close" :disabled="savingEdit" @click="closeEdit">Cancelar</v-btn><v-btn class="edit-save-button" color="primary" variant="flat" prepend-icon="mdi-content-save-outline" :disabled="savingEdit || !editValid || !editHasChanges" :loading="savingEdit" @click="saveEdit">Guardar cambios</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog :model-value="!!confirmDisable" max-width="480" persistent><v-card v-if="confirmDisable" class="dialog-card vehicle-deactivate-dialog"><header class="vehicle-deactivate-dialog__header"><div class="vehicle-deactivate-dialog__header-icon"><v-icon icon="mdi-car" size="25" /></div><div><h2>Desactivar vehículo</h2><p>Confirma esta acción antes de continuar.</p></div></header><v-card-text class="vehicle-deactivate-dialog__content"><v-icon class="vehicle-deactivate-dialog__warning" icon="mdi-alert-circle-outline" size="58"/><h3>¿Seguro que deseas <span>dar de baja</span> este vehículo?</h3><strong class="vehicle-deactivate-dialog__name">{{confirmDisable.make}} {{confirmDisable.model}} <span>{{confirmDisable.plate || 'Sin placas'}}</span></strong><p>El vehículo dejará de estar disponible para nuevas operaciones. Su información y fotografías se conservarán.</p></v-card-text><v-card-actions class="vehicle-deactivate-dialog__actions"><v-spacer /><v-btn class="vehicle-deactivate-dialog__cancel" variant="outlined" prepend-icon="mdi-close" :disabled="disabling" @click="confirmDisable=null">Cancelar</v-btn><v-btn class="vehicle-deactivate-dialog__confirm" variant="flat" prepend-icon="mdi-car-off" :loading="disabling" :disabled="disabling" @click="disable">Desactivar</v-btn></v-card-actions></v-card></v-dialog><v-snackbar :model-value="!!message" color="success" @update:model-value="message=''">{{ message }}</v-snackbar>
  </v-container>
</template>

<style scoped>
.page-shell{max-width:1320px;padding:38px 32px 64px}.page-header{margin-bottom:28px}.header-row,.dialog-heading,.details-hero,.section-title,.owner-card,.address-line,.workshop-banner,.vehicle-mobile__top,.mobile-actions{display:flex;gap:14px;align-items:center}.grow{min-width:0;flex:1}.header-icon,.metric-icon,.details-hero__icon,.mini-car{display:grid;place-items:center;flex:none;border-radius:13px;background:#edf3ff;color:#3867de}.header-icon{width:52px;height:52px}.eyebrow{margin:0 0 8px;color:#3364a2;font-weight:800;letter-spacing:1.3px;font-size:.72rem}.page-header h1{margin:0;color:#172b4d;font-size:clamp(1.8rem,2.6vw,2.3rem);font-weight:800}.subtitle,.table-heading p,.dialog-heading p,.section-title p{margin:5px 0 0;color:#66758b;font-size:.88rem}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-bottom:24px}.metric,.module-card,.dialog-card{border:1px solid #e4e9f2;border-radius:16px;background:#fff;box-shadow:0 12px 28px rgba(23,43,77,.05)}.metric{min-height:132px;padding:20px;display:flex;flex-direction:column;gap:8px}.metric-icon{width:40px;height:40px}.metric-icon.green{background:#e7f6ed;color:#25834a}.metric-icon.amber{background:#fff4df;color:#b87920}.metric strong{font-size:1.75rem;color:#172b4d}.metric span{color:#748197;font-size:.82rem}.table-heading{padding:24px 24px 18px}.table-heading h2,.dialog-heading h2,.details-hero h2,.section-title h3{margin:0;color:#172b4d;font-size:1.1rem}.filter-row{display:grid;grid-template-columns:minmax(260px,1.4fr) minmax(180px,.7fr) minmax(220px,1fr);gap:14px}.vehicle-table :deep(th){height:50px;background:#f4f7fc;color:#64748b;font-size:.71rem;font-weight:800;letter-spacing:.5px;text-transform:uppercase;white-space:nowrap}.vehicle-table :deep(td){padding-top:14px!important;padding-bottom:14px!important;border-color:#edf0f5!important}.vehicle-cell,.person-cell,.workshop-cell{display:flex;align-items:center;gap:10px;min-width:140px}.mini-car{width:38px;height:38px;border-radius:11px}.vehicle-cell strong,.vehicle-cell span,.vehicle-cell small,.person-cell span,.workshop-cell span{display:block;line-height:1.3}.vehicle-cell strong{color:#263a58;font-size:.9rem}.vehicle-cell span,.person-cell span,.workshop-cell span{color:#5f6f85;font-size:.78rem}.vehicle-cell small{margin-top:3px;color:#8a97a9;font-size:.71rem;letter-spacing:.15px}.person-cell{max-width:170px}.person-cell span,.workshop-cell span{font-weight:600}.workshop-cell{max-width:190px}.actions{display:flex;justify-content:flex-end;gap:6px}.empty-row{padding:42px 20px!important;display:flex;justify-content:center;align-items:center;gap:10px;color:#718096}.mobile-list{display:none}.details-hero{padding:26px 28px 22px;border-bottom:1px solid #edf0f5;align-items:flex-start}.details-hero__icon{width:56px;height:56px}.details-hero h2{font-size:1.35rem}.vin-line{display:flex;align-items:center;gap:6px;margin:8px 0 0;color:#667993;font-size:.83rem}.details-content{padding:24px 28px 8px}.details-section+.details-section{margin-top:28px}.section-title{align-items:flex-start;margin-bottom:14px}.section-title h3{font-size:1rem}.owner-card{padding:16px;border:1px solid #e8edf5;border-radius:14px;background:#f8faff;align-items:center}.owner-card strong,.owner-card span{display:block}.owner-card strong{color:#263a58}.owner-card span{margin-top:3px;color:#66758b;font-size:.82rem}.owner-contact{display:grid;gap:5px;min-width:min(320px,45%)}.owner-contact span{display:flex;align-items:center;gap:6px;overflow-wrap:anywhere}.address-line{margin-top:10px;padding:10px 2px;color:#5f6f85;font-size:.82rem}.spec-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.spec-grid>div{min-height:70px;padding:12px;border:1px solid #e8edf5;border-radius:12px;background:#fff}.spec-grid span,.workshop-banner span,.created-date span{display:block;color:#748197;font-size:.72rem;font-weight:700}.spec-grid strong,.workshop-banner strong,.created-date strong{display:block;margin-top:5px;color:#263a58;font-size:.86rem}.workshop-banner{margin-top:14px;padding:14px 16px;border-radius:13px;background:#edf3ff;color:#3867de}.workshop-banner>div{min-width:0}.created-date{margin-left:auto;padding-left:16px;border-left:1px solid #cbd8ef}.photo-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px}.vehicle-photo{border:1px solid #e3eaf5;border-radius:12px;background:#f3f6fb}.photo-placeholder{height:100%;display:grid;place-items:center}.no-photos{min-height:120px;border:1px dashed #cdd7e6;border-radius:14px;display:flex;flex-direction:column;gap:8px;align-items:center;justify-content:center;color:#78879b;font-size:.85rem}.dialog-actions{padding:18px 28px 22px}.vehicle-mobile{padding:15px;border-radius:0;border-bottom:1px solid #e8edf5}.vehicle-mobile:last-child{border-bottom:0}.vehicle-mobile strong,.vehicle-mobile span{display:block}.vehicle-mobile strong{color:#263a58}.vehicle-mobile span{color:#64748b;font-size:.78rem}.vehicle-mobile p{display:flex;gap:7px;align-items:center;margin:10px 0 0;color:#64748b;font-size:.8rem}.mobile-actions{margin-top:14px}.mobile-actions .v-spacer{flex:1}.edit-content{padding:24px 28px 8px}.readonly-association{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}.readonly-association>div{padding:13px;border:1px solid #dbe7f7;border-radius:12px;background:#f4f8ff}.readonly-association span{display:block;color:#687994;font-size:.74rem;font-weight:700}.readonly-association strong{display:flex;align-items:center;gap:6px;margin-top:6px;color:#263a58;font-size:.86rem}.edit-help{margin:0 0 16px;color:#66758b;font-size:.82rem}@media(max-width:900px){.desktop-table{display:none}.mobile-list{display:block}.filter-row{grid-template-columns:1fr}.spec-grid{grid-template-columns:repeat(2,1fr)}.owner-card{align-items:flex-start;flex-wrap:wrap}.owner-contact{width:100%;min-width:100%;padding-left:66px}.metrics{grid-template-columns:1fr 1fr}}@media(max-width:600px){.page-shell{padding:24px 16px 42px}.metrics{grid-template-columns:1fr;gap:12px}.metric{min-height:104px}.table-heading{padding:20px 18px 14px}.details-hero,.details-content,.dialog-actions,.edit-content{padding-left:18px;padding-right:18px}.spec-grid,.readonly-association{grid-template-columns:1fr}.workshop-banner{align-items:flex-start}.created-date{margin-left:0;padding-left:0;border-left:0}.owner-contact{padding-left:0}.details-hero__icon{width:48px;height:48px}}
</style>
<style scoped>
.vehicle-details { display:flex; flex-direction:column; max-height:calc(100dvh - 48px); overflow:hidden; border-radius:18px; background:#fff; }
.vehicle-details::before { display:none!important; }
.vehicle-details__header { display:flex; align-items:flex-start; gap:15px; flex:none; padding:25px 28px 22px; border-bottom:1px solid #e3e9f1; background:#fff; }
.vehicle-details__icon { display:grid; place-items:center; width:52px; height:52px; flex:none; border-radius:13px; background:#eaf2ff; color:#2850e8; }
.vehicle-details__divider { align-self:stretch; width:2px; flex:none; border-radius:2px; background:#dda34e; }
.vehicle-details__eyebrow { margin:1px 0 5px; color:#52709e; font-size:.72rem; font-weight:800; letter-spacing:1.15px; }
.vehicle-details__header h2 { margin:0; color:#172b4d; font-size:1.48rem; font-weight:800; line-height:1.2; }
.vehicle-details__vin { display:flex; align-items:center; gap:6px; margin:8px 0 0; color:#637794; font-size:.82rem; }
.vehicle-details__vin .v-icon { color:#2850e8; }
.vehicle-details__close { margin:-6px -8px 0 0; color:#6c7b90; border-radius:9px; }
.vehicle-details__close:hover { background:rgba(198,70,70,.10); color:#c64747; }
.vehicle-details__content { flex:1 1 auto; min-height:0; overflow-y:auto; overflow-x:hidden; overscroll-behavior:contain; padding:25px 28px 22px; }
.vehicle-details__section + .vehicle-details__section { margin-top:30px; }
.vehicle-details__section-heading { display:flex; align-items:flex-start; gap:11px; margin-bottom:14px; }
.vehicle-details__section-icon { display:grid; place-items:center; width:38px; height:38px; flex:none; border-radius:50%; background:#f8e9ce; color:#2850e8; }
.vehicle-details__section-heading h3 { margin:1px 0 0; color:#1d365c; font-size:1rem; font-weight:800; }
.vehicle-details__section-heading p { margin:4px 0 0; color:#718096; font-size:.83rem; }
.vehicle-owner-card { display:flex; align-items:center; gap:14px; min-height:82px; padding:14px 16px; border:1px solid #d8e6f6; border-radius:15px; background:#f1f7ff; }
.vehicle-owner-card__avatar { flex:none; background:#dceaff; color:#2850e8; font-weight:800; }
.vehicle-owner-card strong,.vehicle-owner-card span { display:block; }
.vehicle-owner-card strong { color:#1e385e; font-size:.95rem; }
.vehicle-owner-card .grow>span { margin-top:4px; color:#64748b; font-size:.82rem; }
.vehicle-owner-card__contact { display:grid; gap:6px; min-width:min(320px,42%); color:#536d90; font-size:.81rem; }
.vehicle-owner-card__contact span { display:flex; align-items:center; gap:7px; overflow-wrap:anywhere; }
.vehicle-owner-card__contact .v-icon { color:#2850e8; }
.vehicle-owner-address { display:flex; align-items:flex-start; gap:7px; margin:11px 3px 0; color:#667992; font-size:.82rem; line-height:1.45; }
.vehicle-owner-address .v-icon { flex:none; margin-top:1px; color:#2850e8; }
.vehicle-details__spec-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
.vehicle-details__spec-grid article { min-height:78px; padding:14px; border:1px solid #dfe6ef; border-radius:13px; background:#fff; }
.vehicle-details__spec-grid span { display:block; color:#71819a; font-size:.73rem; font-weight:700; }
.vehicle-details__spec-grid strong { display:block; margin-top:6px; color:#1d365c; font-size:.91rem; font-weight:800; overflow-wrap:anywhere; }
.vehicle-details__photo-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(178px,1fr)); gap:14px; }
.vehicle-details__photo { overflow:hidden; border:1px solid #dbe4ef; border-radius:13px; background:#eef3f9; box-shadow:0 4px 12px rgba(23,43,77,.06); }
.vehicle-details__photo :deep(.v-img__img) { transition:transform 300ms ease; }
.vehicle-details__photo:hover :deep(.v-img__img) { transform:scale(1.05); }
.vehicle-details__empty-photos { min-height:118px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; border:1px dashed #cbd8e7; border-radius:14px; color:#718096; font-size:.84rem; }
.vehicle-details__empty-photos .v-icon { color:#6b8bb8; }
.vehicle-details__actions { flex:none; padding:16px 28px 20px; border-top:1px solid #e2e8f0; background:#fff; }
.vehicle-details__close-button { min-width:138px; min-height:42px; border-color:#cbd5e1!important; color:#475569!important; font-weight:800; text-transform:none; }
.vehicle-details__close-button:hover,.vehicle-details__close-button:focus-visible { border-color:#c64747!important; background:rgba(198,70,70,.10)!important; color:#b93838!important; }
:global(.v-theme--dark) .vehicle-details { border-color:#374863; background:#1a2639; }
:global(.v-theme--dark) .vehicle-details__header,:global(.v-theme--dark) .vehicle-details__actions { border-color:#374863; background:#1a2639; }
:global(.v-theme--dark) .vehicle-details__header h2,:global(.v-theme--dark) .vehicle-details__section-heading h3,:global(.v-theme--dark) .vehicle-details__spec-grid strong,:global(.v-theme--dark) .vehicle-owner-card strong { color:#e7eefb; }
:global(.v-theme--dark) .vehicle-details__content { background:#1a2639; }
:global(.v-theme--dark) .vehicle-owner-card { border-color:#385373; background:#22334b; }
:global(.v-theme--dark) .vehicle-details__spec-grid article { border-color:#374863; background:#202d41; }
:global(.v-theme--dark) .vehicle-details__eyebrow,:global(.v-theme--dark) .vehicle-details__vin,:global(.v-theme--dark) .vehicle-details__section-heading p,:global(.v-theme--dark) .vehicle-owner-address,:global(.v-theme--dark) .vehicle-owner-card .grow>span,:global(.v-theme--dark) .vehicle-owner-card__contact,:global(.v-theme--dark) .vehicle-details__spec-grid span { color:#b4c1d4; }
:global(.v-theme--dark) .vehicle-details__empty-photos { border-color:#40516b; color:#b4c1d4; }
@media(max-width:700px) { .vehicle-details { max-height:calc(100dvh - 24px); } .vehicle-details__header,.vehicle-details__content,.vehicle-details__actions { padding-left:18px; padding-right:18px; } .vehicle-details__header { gap:11px; padding-top:20px; } .vehicle-details__icon { width:46px; height:46px; } .vehicle-details__header h2 { font-size:1.22rem; } .vehicle-owner-card { align-items:flex-start; flex-wrap:wrap; } .vehicle-owner-card__contact { width:100%; min-width:100%; padding-left:68px; } .vehicle-details__spec-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media(max-width:420px) { .vehicle-details__divider { display:none; } .vehicle-details__vin { overflow-wrap:anywhere; } .vehicle-owner-card__contact { padding-left:0; } .vehicle-details__close-button { width:100%; } }
</style>
<style scoped>
.vehicle-update-success,.vehicle-deactivation-success{border:1px solid rgba(35,126,24,.2)!important;background:#eaf7ea!important;color:#237e18!important;font-weight:700}.vehicle-update-success :deep(.v-icon),.vehicle-deactivation-success :deep(.v-icon){color:#237e18!important}.vehicle-deactivate-dialog{text-align:center}.vehicle-deactivate-dialog:before{display:none!important}.vehicle-deactivate-dialog__header{display:flex;align-items:center;gap:13px;padding:22px 26px;border-bottom:1px solid #f0d9dc;background:#fffafa;text-align:left}.vehicle-deactivate-dialog__header-icon{display:grid;place-items:center;width:44px;height:44px;border-radius:12px;background:#fdebed;color:#2850e8}.vehicle-deactivate-dialog__header h2{margin:0;color:#142b50;font-size:1.14rem;font-weight:800}.vehicle-deactivate-dialog__header p{margin:4px 0 0;color:#64748b;font-size:.82rem}.vehicle-deactivate-dialog__content{padding:24px 30px 22px}.vehicle-deactivate-dialog__warning{display:block;margin:0 auto 13px;color:#dc3545}.vehicle-deactivate-dialog__content h3{margin:0;color:#142b50;font-size:1.14rem;line-height:1.4}.vehicle-deactivate-dialog__content h3 span{color:#dc3545}.vehicle-deactivate-dialog__name{display:block;margin:12px 0 8px;color:#475569;font-size:.92rem}.vehicle-deactivate-dialog__name span{margin-left:4px;color:#64748b;font-weight:600}.vehicle-deactivate-dialog__content p{max-width:360px;margin:0 auto;color:#64748b;font-size:.86rem;line-height:1.55}.vehicle-deactivate-dialog__actions{padding:16px 26px 22px;border-top:1px solid #edf0f4;background:#fff}.vehicle-deactivate-dialog__cancel{min-width:112px;border-color:#cbd5e1!important;background:#fff!important;color:#475569!important}.vehicle-deactivate-dialog__cancel:hover:not(.v-btn--disabled),.vehicle-deactivate-dialog__cancel:focus-visible:not(.v-btn--disabled){border-color:#334155!important;background:#334155!important;color:#fff!important}.vehicle-deactivate-dialog__confirm{min-width:126px;background:linear-gradient(135deg,#dc3545,#b91c2c)!important;color:#fff!important;box-shadow:0 7px 16px rgba(185,28,44,.22)}.vehicle-deactivate-dialog__confirm:hover:not(.v-btn--disabled),.vehicle-deactivate-dialog__confirm:focus-visible:not(.v-btn--disabled){background:linear-gradient(135deg,#b91c2c,#8f1724)!important;color:#fff!important}@media(max-width:600px){.vehicle-deactivate-dialog__actions{gap:8px}.vehicle-deactivate-dialog__actions .v-btn{flex:1;min-width:0}}:global(.v-theme--dark) .vehicle-update-success,:global(.v-theme--dark) .vehicle-deactivation-success{background:rgba(35,126,24,.2)!important;border-color:rgba(104,190,94,.36)!important;color:#c9edc4!important}:global(.v-theme--dark) .vehicle-update-success :deep(.v-icon),:global(.v-theme--dark) .vehicle-deactivation-success :deep(.v-icon){color:#8fd68a!important}
</style>

<style scoped>
.details-hero {
  background: linear-gradient(135deg, #f5f9ff 0%, #edf4ff 100%);
  border-bottom-color: #dfe9f7;
}
.vehicle-edit { display:flex; flex-direction:column; max-height:calc(100dvh - 48px); overflow:hidden; }
.vehicle-edit__header { display:flex; align-items:center; gap:14px; flex:none; padding:22px 28px 20px; border-bottom:1px solid #e1e8f0; background:#fbfcfe; }
.edit-header-icon { display:grid; place-items:center; width:44px; height:44px; flex:none; border-radius:12px; background:#fff3dc; color:#2f63c7; }
.vehicle-edit__heading { min-width:0; padding-left:14px; border-left:3px solid #d5a055; }
.vehicle-edit__heading h2 { margin:0; color:#172b4d; font-size:1.22rem; font-weight:800; }
.vehicle-edit__heading p { margin:4px 0 0; color:#66758b; font-size:.84rem; }
.edit-close-button { color:#718096; border-radius:9px; transition:background-color .18s ease,color .18s ease; }
.edit-close-button:hover:not(.v-btn--disabled) { background:rgba(198,70,70,.11); color:#c64747; }
.vehicle-edit .edit-content { flex:0 1 auto; max-height:min(540px, calc(100dvh - 210px)); min-height:0; overflow-x:hidden; overflow-y:auto; overscroll-behavior:contain; padding:24px 28px 14px; }
.linked-info,.vehicle-data { padding:18px; border:1px solid #e4eaf1; border-radius:16px; background:#fff; }
.vehicle-data { margin-top:18px; }
.edit-section-heading,.section-heading__title { display:flex; align-items:center; gap:8px; }
.edit-section-heading { margin-bottom:14px; color:#2f63c7; }
.edit-section-heading h3 { margin:0; color:#1e3557; font-size:.98rem; font-weight:800; }
.edit-section-heading--data { justify-content:space-between; }
.required-chip { background:#fff3dc; color:#9a6419; font-weight:700; }
.readonly-association { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin:0; }
.association-card { display:flex; align-items:center; gap:11px; min-height:76px; padding:14px; border:1px solid #dbe7f7; border-radius:13px; background:#eff6ff; }
.association-card>.v-icon { flex:none; color:#2f63c7; }
.association-card span,.vin-panel__value span,.additional-data>p { display:block; color:#687994; font-size:.73rem; font-weight:700; }
.association-card strong,.vin-panel__value strong { display:block; margin-top:5px; overflow-wrap:anywhere; color:#203a5e; font-size:.87rem; }
.vin-panel { display:flex; align-items:center; gap:11px; margin-top:12px; padding:13px 14px; border:1px solid #f0dbb3; border-radius:13px; background:#fff8e9; color:#aa751d; }
.vin-panel__value { min-width:0; flex:1; }
.vin-lock { flex:none; background:#f4e6c7; color:#85601d; font-weight:700; }
.vin-note { display:flex; align-items:center; gap:6px; margin:8px 2px 0; color:#7d8692; font-size:.77rem; }
.edit-fields { margin-top:4px; }
.edit-fields :deep(.v-col) { padding-top:8px; padding-bottom:8px; }
.edit-fields :deep(.v-field) { border-radius:10px; }
.edit-photos { margin:24px 0 8px; padding-top:20px; border-top:1px solid #e6ebf1; }
.section-heading__icon { display:grid; place-items:center; width:38px; height:38px; flex:none; border-radius:50%; background:#f8e9ce; color:#2850e8; }
.sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
.vehicle-photo-cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(164px,1fr)); gap:14px; }
.vehicle-photo-card { position:relative; overflow:hidden; min-height:154px; border:1px solid #b8d2f4; border-radius:14px; background:#eef3fc; box-shadow:0 4px 12px rgba(20,43,80,.05); }
.vehicle-photo-card .vehicle-photo { height:154px!important; border:0; border-radius:13px; }
.photo-principal { position:absolute; top:10px; left:10px; display:inline-flex; align-items:center; gap:5px; padding:6px 10px; border-radius:999px; background:rgba(20,45,80,.85); color:#fff; font-size:.74rem; font-weight:800; line-height:1; box-shadow:0 2px 7px rgba(20,43,80,.2); }
.photo-principal :deep(.v-icon) { color:#ffc247!important; }
.vehicle-photo-card__actions { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; gap:10px; background:rgba(20,43,80,.48); opacity:0; transition:opacity .18s ease; }
.vehicle-photo-card:hover .vehicle-photo-card__actions,.vehicle-photo-card:focus-within .vehicle-photo-card__actions { opacity:1; }
.vehicle-photo-card__actions .v-btn { width:40px; height:40px; border-radius:50%; background:#e8f0ff!important; color:#2850e8!important; box-shadow:0 5px 12px rgba(20,43,80,.2); }
.vehicle-photo-card__actions .v-btn:last-child { background:#fdebed!important; color:#dc3545!important; }
.add-photo-card { min-height:154px; border:1px dashed #8daeff; border-radius:14px; background:#eef3fc; color:#2850e8; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:7px; cursor:pointer; font:inherit; font-weight:800; }
.add-photo-card small { color:#64748b; font-size:.76rem; font-weight:600; }
.edit-actions { flex:none; gap:10px; padding:16px 28px 20px; border-top:1px solid #e1e8f0; background:#fbfcfe; }
.edit-cancel-button,.edit-save-button { min-width:148px; min-height:42px; border-radius:10px; font-weight:700; letter-spacing:.1px; text-transform:none; }
.edit-cancel-button { border-color:#cbd5e1; color:#536276; transition:background-color .18s ease,border-color .18s ease,color .18s ease; }
.edit-cancel-button:hover:not(.v-btn--disabled) { background:rgba(198,70,70,.10)!important; border-color:#c64747!important; color:#b93838!important; }
.edit-save-button { background:#2850e8!important; color:#fff!important; box-shadow:0 8px 16px rgba(40,80,232,.20); transition:background-color .18s ease,box-shadow .18s ease; }
.edit-save-button:hover:not(.v-btn--disabled) { background:#1f42c7!important; box-shadow:0 10px 18px rgba(40,80,232,.28); }
.edit-save-button:active:not(.v-btn--disabled) { background:#253b60!important; color:#fff!important; }
.edit-save-button.v-btn--loading { background:#253b60!important; color:#fff!important; }
.edit-save-button:focus-visible,.edit-cancel-button:focus-visible,.edit-close-button:focus-visible { outline:3px solid rgba(45,99,232,.35); outline-offset:2px; }
.edit-save-button.v-btn--disabled { background:#9aa8c8!important; color:#f7f9ff!important; box-shadow:none; }
@media(max-width:600px) {
  .vehicle-edit { max-height:calc(100dvh - 24px); }
  .vehicle-edit .edit-content { max-height:calc(100dvh - 220px); }
  .vehicle-edit__header,.vehicle-edit .edit-content,.edit-actions { padding-left:18px; padding-right:18px; }
  .vehicle-edit__heading { padding-left:10px; }
  .vehicle-edit__heading p { font-size:.77rem; }
  .readonly-association { grid-template-columns:1fr; }
  .vin-panel { align-items:flex-start; flex-wrap:wrap; }
  .vin-lock { margin-left:33px; }
  .edit-section-heading--data { align-items:flex-start; gap:10px; flex-direction:column; }
  .edit-actions { flex-wrap:wrap; }
  .edit-actions .v-spacer { display:none; }
  .edit-cancel-button,.edit-save-button { flex:1 1 100%; }
}
</style>

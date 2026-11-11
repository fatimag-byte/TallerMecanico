import api from './api'
import type { Vehicle, VehiclePayload, VehicleUpdatePayload } from '../types'

export async function createVehicle(workshopId: number, customerId: number, payload: VehiclePayload) {
  const { data } = await api.post<{ id: number; vin: string }>('/vehicles', payload, { params: { workshop_id: workshopId, customer_id: customerId } })
  return data
}
export async function checkVehicleVin(vin: string) {
  const { data } = await api.get<{ vin: string; duplicate: boolean; vehicle_id: number | null }>('/vehicles/check-vin', { params: { vin } })
  return data
}
export async function uploadVehiclePhotos(vehicleId: number, files: File[]) {
  const form = new FormData(); files.forEach(file => form.append('files', file))
  const { data } = await api.post(`/vehicles/${vehicleId}/photos`, form)
  return data
}
export async function deleteVehiclePhoto(vehicleId: number, photoId: number) {
  await api.delete(`/vehicles/${vehicleId}/photos/${photoId}`)
}
export async function listVehicles(params: { workshop_id?: number; customer_id?: number; search?: string; status_filter?: string }) {
  const { data } = await api.get<Vehicle[]>('/vehicles', { params })
  return data
}
export async function getVehicle(vehicleId: number) {
  const { data } = await api.get<Vehicle>(`/vehicles/${vehicleId}`)
  const photos = await Promise.all((data.photos || []).map(async photo => {
    const image = await api.get(photo.url.replace(/^\/api/, ''), { responseType: 'blob' })
    return { ...photo, url: URL.createObjectURL(image.data) }
  }))
  return { ...data, photos }
}
export async function setVehicleStatus(vehicleId: number, active: boolean) { const { data } = await api.patch(`/vehicles/${vehicleId}/status`, null, { params: { active } }); return data }
export async function updateVehicle(vehicleId: number, payload: VehicleUpdatePayload) {
  const { data } = await api.put<Vehicle>(`/vehicles/${vehicleId}`, payload)
  return data
}

import api from './api'
import type { Customer, CustomerPayload, Workshop } from '../types'

export async function activeWorkshops() {
  const { data } = await api.get<Workshop[]>('/workshops', { params: { status_filter: 'activos' } })
  return data
}
export async function listCustomers(params: { workshop_id?: number; search?: string; status_filter?: string }) {
  const { data } = await api.get<Customer[]>('/customers', { params })
  return data
}
export async function findDuplicates(workshopId: number, payload: CustomerPayload, excludeId?: number) {
  const { data } = await api.post<{ exact: Customer[]; possible: Customer[]; contact_in_use: boolean }>('/customers/duplicates', payload, { params: { workshop_id: workshopId, exclude_id: excludeId } })
  return data
}
export async function createCustomer(workshopId: number, payload: CustomerPayload) {
  const { data } = await api.post<Customer>('/customers', payload, { params: { workshop_id: workshopId } })
  return data
}
export async function updateCustomer(customerId: number, workshopId: number, payload: CustomerPayload) {
  const { data } = await api.put<Customer>(`/customers/${customerId}`, payload, { params: { workshop_id: workshopId } })
  return data
}
export async function setCustomerStatus(customerId: number, workshopId: number, active: boolean) {
  const { data } = await api.patch<Customer>(`/customers/${customerId}/status`, null, { params: { workshop_id: workshopId, active } })
  return data
}

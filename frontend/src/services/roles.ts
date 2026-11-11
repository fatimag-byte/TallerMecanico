import api from './api'
import type { Permission, Role, RoleUsers } from '../types'

export interface RolePayload { name: string; description: string; permission_ids: number[] }

export const listPermissions = () => api.get<Permission[]>('/permissions').then(({ data }) => data)
export const listRoles = () => api.get<Role[]>('/roles').then(({ data }) => data)
export const createRole = (payload: RolePayload) => api.post<Role>('/roles', payload).then(({ data }) => data)
export const updateRole = (id: number, payload: RolePayload) => api.put<Role>(`/roles/${id}`, payload).then(({ data }) => data)
export const deleteRole = (id: number) => api.delete(`/roles/${id}`)
export const checkRoleName = (name: string) => api.get<{ available: boolean }>('/roles/check-name', { params: { name } }).then(({ data }) => data)
export const listRoleUsers = (id: number) => api.get<RoleUsers>(`/roles/${id}/users`).then(({ data }) => data)
export const assignUserToRole = (roleId: number, userId: number) => api.post<RoleUsers>(`/roles/${roleId}/users/${userId}`).then(({ data }) => data)
export const removeUserFromRole = (roleId: number, userId: number) => api.delete<RoleUsers>(`/roles/${roleId}/users/${userId}`).then(({ data }) => data)

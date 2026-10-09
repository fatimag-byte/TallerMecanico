import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { AuthResponse, User } from '../types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api' })
let accessToken = sessionStorage.getItem('access_token')
let refreshing: Promise<string> | null = null

export const authStorage = {
  get refreshToken() { return localStorage.getItem('refresh_token') },
  save(data: AuthResponse) { accessToken = data.access_token; sessionStorage.setItem('access_token', data.access_token); localStorage.setItem('refresh_token', data.refresh_token); localStorage.setItem('access_expires_at', data.expires_at); localStorage.setItem('user', JSON.stringify(data.user)) },
  clear() { accessToken = null; sessionStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); localStorage.removeItem('access_expires_at'); localStorage.removeItem('user') },
  get user(): User | null { const raw = localStorage.getItem('user'); return raw ? JSON.parse(raw) : null },
}

export async function refreshSession(): Promise<string> {
  const token = authStorage.refreshToken
  if (!token) throw new Error('No hay una sesión para renovar.')
  const { data } = await axios.post<AuthResponse>(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: token })
  authStorage.save(data)
  return data.access_token
}

api.interceptors.request.use((config) => { if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`; return config })
api.interceptors.response.use(undefined, async (error: AxiosError<{ detail: string }>) => {
  const original = error.config as InternalAxiosRequestConfig & { _retried?: boolean }
  if (error.response?.status !== 401 || original._retried || original.url?.includes('/auth/refresh')) return Promise.reject(error)
  const token = authStorage.refreshToken
  if (!token) return Promise.reject(error)
  original._retried = true
  try {
    refreshing ??= refreshSession().finally(() => { refreshing = null })
    original.headers.Authorization = `Bearer ${await refreshing}`
    return api(original)
  } catch (refreshError) { authStorage.clear(); window.dispatchEvent(new Event('auth-expired')); return Promise.reject(refreshError) }
})
export default api

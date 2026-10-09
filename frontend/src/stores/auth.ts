import { computed, reactive } from 'vue'
import api, { authStorage } from '../services/api'
import type { AuthResponse, User } from '../types'

const state = reactive<{ user: User | null; loading: boolean }>({ user: authStorage.user, loading: false })
export const useAuth = () => {
  const authenticated = computed(() => !!state.user)
  async function authenticate(path: 'login' | 'register', payload: Record<string, string>) { state.loading = true; try { const { data } = await api.post<AuthResponse>(`/auth/${path}`, payload); authStorage.save(data); state.user = data.user; return data } finally { state.loading = false } }
  async function logout() { const token = authStorage.refreshToken; try { if (token) await api.post('/auth/logout', { refresh_token: token }) } finally { authStorage.clear(); state.user = null } }
  return { state, authenticated, authenticate, logout }
}

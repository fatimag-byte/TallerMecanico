import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from './stores/auth'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import DashboardView from './views/DashboardView.vue'
import ForgotPasswordView from './views/ForgotPasswordView.vue'
import ResetPasswordView from './views/ResetPasswordView.vue'

const router = createRouter({ history: createWebHistory(), routes: [
  { path: '/', redirect: '/dashboard' }, { path: '/login', component: LoginView, meta: { public: true } }, { path: '/registro', component: RegisterView, meta: { public: true } }, { path: '/recuperar-contrasena', component: ForgotPasswordView, meta: { public: true } }, { path: '/restablecer', component: ResetPasswordView, meta: { public: true } }, { path: '/dashboard', component: DashboardView }
] })
router.beforeEach((to) => { const { authenticated } = useAuth(); if (!to.meta.public && !authenticated.value) return '/login'; if (to.meta.public && authenticated.value) return '/dashboard' })
export default router

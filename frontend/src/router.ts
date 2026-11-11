import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from './stores/auth'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import DashboardView from './views/DashboardView.vue'
import ForgotPasswordView from './views/ForgotPasswordView.vue'
import ResetPasswordView from './views/ResetPasswordView.vue'
import CreateRoleView from './views/CreateRoleView.vue'
import ManageRolesView from './views/ManageRolesView.vue'
import WorkshopRegisterView from './views/WorkshopRegisterView.vue'
import WorkshopsManageView from './views/WorkshopsManageView.vue'
import CustomerRegisterView from './views/CustomerRegisterView.vue'
import CustomersManageView from './views/CustomersManageView.vue'
import VehicleRegisterView from './views/VehicleRegisterForm.vue'
import VehiclesManageView from './views/VehiclesManageView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/registro', component: RegisterView, meta: { public: true } },
    { path: '/recuperar-contrasena', component: ForgotPasswordView, meta: { public: true } },
    { path: '/restablecer', component: ResetPasswordView, meta: { public: true } },
    { path: '/dashboard', component: DashboardView },
    { path: '/talleres', component: WorkshopRegisterView, meta: { requiresManage: true } },
    { path: '/talleres/administracion', component: WorkshopsManageView, meta: { requiresOperational: true } },
    { path: '/taller/registro', redirect: '/talleres' },
    { path: '/clientes/registro', component: CustomerRegisterView, meta: { requiresOperational: true } },
    { path: '/clientes', component: CustomersManageView, meta: { requiresOperational: true } },
    { path: '/vehiculos/registro', component: VehicleRegisterView, meta: { requiresOperational: true } },
    { path: '/vehiculos', component: VehiclesManageView, meta: { requiresOperational: true } },
    { path: '/roles', component: ManageRolesView, meta: { requiresManage: true } },
    { path: '/roles/nuevo', component: CreateRoleView, meta: { requiresManage: true } }
  ]
})

router.beforeEach((to) => {
  const { authenticated, state } = useAuth()
  if (!to.meta.public && !authenticated.value) return '/login'
  if (to.meta.requiresManage && !state.user?.permissions.includes('users:manage')) return '/dashboard'
  if (to.meta.requiresOperational && !state.user?.permissions.some(item => ['customers:manage', 'workshops:manage', 'vehicles:manage'].includes(item))) return '/dashboard'
  if (to.meta.public && authenticated.value) return '/dashboard'
})

export default router

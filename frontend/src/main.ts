import { createApp } from 'vue'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import './styles/vehicle-icons.css'
import './styles/theme.css'
import { createVuetify } from 'vuetify'
import { es } from 'vuetify/locale'
import App from './App.vue'
import router from './router'

createApp(App).use(createVuetify({
  locale: { locale: 'es', fallback: 'es', messages: { es } },
  theme: { defaultTheme: 'light', themes: {
  light: { colors: { primary: '#2850E8', secondary: '#DDA34E', success: '#237E18', surface: '#FFFFFF', background: '#F6F8FC', error: '#DC3545' } },
} } })).use(router).mount('#app')

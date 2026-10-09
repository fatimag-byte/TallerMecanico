import { createApp } from 'vue'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import App from './App.vue'
import router from './router'

createApp(App).use(createVuetify({ theme: { defaultTheme: 'light', themes: { light: { colors: { primary: '#3867DE', secondary: '#D9A05B', surface: '#FFFFFF', background: '#F4F6FB', error: '#C62828' } } } } })).use(router).mount('#app')

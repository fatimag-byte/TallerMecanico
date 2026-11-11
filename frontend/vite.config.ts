import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true })],
  server: { port: 5173 },
  preview: { allowedHosts: ['just-clarity-production-3a213deb.up.railway.app'] },
})

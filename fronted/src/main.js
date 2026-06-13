/**
 * src/main.js
 * ────────────
 * Application entry point for LinguaIELTS.
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from '@/router/index.js'
import App from '@/App.vue'
import '@/assets/main.css'
import '@/assets/admin-theme.css'
import { setupAdminTextareaAutoGrow } from '@/utils/adminTextareaAutoGrow.js'

const savedTheme = localStorage.getItem('lingua-theme') || 'dark'
document.documentElement.setAttribute('data-theme', savedTheme)

const app = createApp(App)
app.use(createPinia())
app.use(router)
setupAdminTextareaAutoGrow(router)
app.mount('#app')

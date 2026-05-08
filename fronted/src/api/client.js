/**
 * src/api/client.js
 * ──────────────────
 * Axios instance pre-configured for the backend API.
 * - Attaches JWT token to every request via request interceptor
 * - Handles 401 responses by clearing auth and redirecting to /login
 */
import axios from 'axios'
import { useAuthStore } from '@/stores/auth.js'
import router from '@/router/index.js'

const apiClient = axios.create({
  baseURL: '/api',           // Vite proxy rewrites /api → http://localhost:8000
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach Bearer token ──────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor: handle 401 globally ─────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — clear state and redirect
      try {
        const authStore = useAuthStore()
        authStore.logout()
      } catch {
        localStorage.removeItem('token')
      }
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default apiClient

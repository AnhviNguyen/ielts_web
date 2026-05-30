/**
 * src/api/client.js
 * Axios instance: JWT, auto-refresh on 401, CSRF + httpOnly refresh cookies.
 */
import axios from 'axios'
import { useAuthStore } from '@/stores/auth.js'
import router from '@/router/index.js'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

function getCsrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token')
}

function getAccessToken() {
  return localStorage.getItem('access_token') || localStorage.getItem('token')
}

function setTokens(accessToken, refreshToken) {
  localStorage.setItem('access_token', accessToken)
  localStorage.removeItem('token')
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken)
  } else {
    localStorage.removeItem('refresh_token')
  }
}

function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
}

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const method = (config.method || 'get').toLowerCase()
    if (['post', 'put', 'patch', 'delete'].includes(method)) {
      const csrf = getCsrfToken()
      if (csrf) {
        config.headers['X-CSRF-Token'] = csrf
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)))
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (err) => {
    const orig = err.config
    if (
      err.response?.status === 401 &&
      orig &&
      !orig._retry &&
      !orig.url?.includes('/auth/refresh') &&
      !orig.url?.includes('/auth/login')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          orig.headers.Authorization = `Bearer ${token}`
          return apiClient(orig)
        })
      }

      orig._retry = true
      isRefreshing = true
      const refreshToken = getRefreshToken()

      try {
        const refreshBody = refreshToken ? { refresh_token: refreshToken } : {}
        const csrf = getCsrfToken()
        const headers = { 'Content-Type': 'application/json' }
        if (csrf) headers['X-CSRF-Token'] = csrf

        const { data } = await axios.post('/api/auth/refresh', refreshBody, {
          withCredentials: true,
          headers,
        })
        setTokens(data.access_token, data.refresh_token)
        apiClient.defaults.headers.common.Authorization = `Bearer ${data.access_token}`
        orig.headers.Authorization = `Bearer ${data.access_token}`
        processQueue(null, data.access_token)
        return apiClient(orig)
      } catch (refreshErr) {
        processQueue(refreshErr, null)
        clearTokens()
        try {
          useAuthStore().logout()
        } catch {
          /* ignore */
        }
        router.push('/login')
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    if (err.response?.status === 401) {
      try {
        useAuthStore().logout()
      } catch {
        clearTokens()
      }
      router.push('/login')
    } else if (error.response?.status === 403 && error.response?.data?.detail === 'Account is locked') {
      try {
        const authStore = useAuthStore()
        authStore.logout()
      } catch {
        localStorage.removeItem('token')
      }
      router.push('/login')
    }
    return Promise.reject(err)
  }
)

export default apiClient

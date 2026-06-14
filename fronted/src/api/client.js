/**
 * src/api/client.js
 * ──────────────────
 * Axios instance with automatic token refresh on 401.
 *
 * Auth flow:
 *   1. Every request carries the access token (Authorization: Bearer …)
 *   2. On 401 (expired) → silently POST /api/auth/refresh (sends httpOnly
 *      refresh cookie automatically) → store new access token → retry
 *   3. If refresh also fails → clear session → redirect /login
 *
 * CSRF: double-submit pattern.
 *   The backend sets a readable csrf_token cookie (non-httpOnly, path=/).
 *   We read it and echo it back in X-CSRF-Token on mutating requests.
 *   /auth/refresh and /auth/logout are exempt on the backend side.
 */
import axios from 'axios'
import { clearTokens, getAccessToken, setTokens } from '@/api/tokenStore.js'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,   // always send cookies (refresh token, csrf_token)
})

// ── CSRF helper ───────────────────────────────────────────────────────────────
function getCsrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

// ── Request interceptor: attach access token + CSRF ───────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
      delete config.headers['content-type']
    }
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const method = (config.method || 'get').toLowerCase()
    if (['post', 'put', 'patch', 'delete'].includes(method)) {
      const csrf = getCsrfToken()
      if (csrf) config.headers['X-CSRF-Token'] = csrf
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Token refresh state ───────────────────────────────────────────────────────
let _refreshing = false
let _pendingQueue = []   // requests waiting while refresh is in progress

function _flushQueue(error, token = null) {
  _pendingQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)))
  _pendingQueue = []
}

// ── Response interceptor: handle 401 / 403 ───────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (err) => {
    const original = err.config
    const status  = err.response?.status

    // ── Automatic token refresh on 401 ──────────────────────────────────────
    const isRefreshEndpoint = original?.url?.includes('/auth/refresh')
    const isLoginEndpoint   = original?.url?.includes('/auth/login')
    const isGoogleEndpoint  = original?.url?.includes('/auth/google')

    if (status === 401 && original && !original._retry && !isRefreshEndpoint && !isLoginEndpoint && !isGoogleEndpoint) {
      // Queue concurrent requests until refresh completes
      if (_refreshing) {
        return new Promise((resolve, reject) => {
          _pendingQueue.push({ resolve, reject })
        }).then((newToken) => {
          original.headers.Authorization = `Bearer ${newToken}`
          return apiClient(original)
        })
      }

      original._retry = true
      _refreshing = true

      try {
        // Use bare axios so this call never goes through the response interceptor
        // (prevents infinite 401 → refresh → 401 loops)
        const { data } = await axios.post(
          '/api/auth/refresh',
          {},
          { withCredentials: true },
        )
        const newToken = data.access_token
        setTokens(newToken)
        apiClient.defaults.headers.common.Authorization = `Bearer ${newToken}`
        original.headers.Authorization = `Bearer ${newToken}`
        _flushQueue(null, newToken)
        return apiClient(original)
      } catch (refreshError) {
        _flushQueue(refreshError, null)
        _forceLogout()
        return Promise.reject(refreshError)
      } finally {
        _refreshing = false
      }
    }

    // ── Refresh token itself is invalid / expired → force logout ────────────
    // Only force logout if we were actively rotating a token (_refreshing),
    // NOT during initial session check from the router guard — that case is
    // handled gracefully by refreshSession()'s own catch block.
    if (status === 401 && isRefreshEndpoint && _refreshing) {
      _flushQueue(new Error('Refresh token expired or revoked'), null)
      _refreshing = false
      _forceLogout()
    }

    // ── Account locked ───────────────────────────────────────────────────────
    if (status === 403 && err.response?.data?.detail === 'Account is locked') {
      _forceLogout()
    }

    return Promise.reject(err)
  },
)

/**
 * Clear local auth state and redirect to login.
 * Lazy-imports the auth store to avoid circular dependency at module load.
 */
async function _forceLogout() {
  try {
    const { useAuthStore } = await import('@/stores/auth.js')
    await useAuthStore().resetLocalAuth()
  } catch {
    clearTokens()
  }
  const { default: router } = await import('@/router/index.js')
  if (router.currentRoute.value.path !== '/login') {
    await router.push('/login')
  }
}

export default apiClient

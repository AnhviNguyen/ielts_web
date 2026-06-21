/** Runtime config injected by docker-entrypoint.sh; falls back to Vite build-time env. */

function runtimeConfig() {
  if (typeof window !== 'undefined' && window.__APP_CONFIG__) {
    return window.__APP_CONFIG__
  }
  return {}
}

export function getApiBaseUrl() {
  const fromRuntime = (runtimeConfig().apiUrl || '').trim()
  if (fromRuntime) return fromRuntime.replace(/\/$/, '')
  const fromEnv = (import.meta.env.VITE_API_URL || '').trim()
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  return '/api'
}

export function getGoogleClientId() {
  const fromRuntime = (runtimeConfig().googleClientId || '').trim()
  if (fromRuntime) return fromRuntime
  return (import.meta.env.VITE_GOOGLE_CLIENT_ID || '').trim()
}

export function getGoogleRedirectUri() {
  const fromRuntime = (runtimeConfig().googleRedirectUri || '').trim()
  if (fromRuntime) return fromRuntime.replace(/\/$/, '')
  const fromEnv = (import.meta.env.VITE_GOOGLE_REDIRECT_URI || '').trim()
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/auth/google/callback`
  }
  return '/auth/google/callback'
}

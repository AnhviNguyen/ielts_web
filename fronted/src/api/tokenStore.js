/**
 * tokenStore.js
 * ─────────────
 * Access token persistence layer.
 *
 * Strategy:
 *   • sessionStorage  → token survives same-tab page reloads
 *   • httpOnly cookie → refresh token is sent automatically by the browser
 *     on /api/auth/refresh calls (set by backend, never readable from JS)
 *
 * On a fresh tab / after tab close:
 *   sessionStorage is empty → auth store calls refreshSession() → backend
 *   validates the httpOnly refresh cookie → issues a new access token.
 */

const SESSION_KEY = 'at'  // short key, value is already opaque JWT

/** Return stored access token, or null if absent. */
export function getAccessToken() {
  try {
    return sessionStorage.getItem(SESSION_KEY) || null
  } catch {
    return null
  }
}

/** Persist access token for the current tab session. */
export function setTokens(accessToken) {
  try {
    if (accessToken) {
      sessionStorage.setItem(SESSION_KEY, accessToken)
    } else {
      sessionStorage.removeItem(SESSION_KEY)
    }
  } catch {
    /* sessionStorage unavailable (e.g. private mode with storage blocked) */
  }
  _clearLegacy()
}

/** Remove access token from storage (called on logout). */
export function clearTokens() {
  try {
    sessionStorage.removeItem(SESSION_KEY)
  } catch {
    /* ignore */
  }
  _clearLegacy()
}

/** Remove old localStorage keys left by previous implementation. */
function _clearLegacy() {
  try {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token')
  } catch {
    /* ignore */
  }
}

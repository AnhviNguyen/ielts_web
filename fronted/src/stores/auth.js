/**
 * src/stores/auth.js
 * ───────────────────
 * Pinia store for authentication state.
 * Handles login, register, logout, profile fetch, and token persistence.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clearTokens, getAccessToken, setTokens as setClientTokens } from '@/api/tokenStore.js'
import { authService } from '@/services/authService.js'

export const useAuthStore = defineStore('auth', () => {
  // ── State ────────────────────────────────────────────────────────────────
  const token   = ref(getAccessToken())
  const profile = ref(null)
  const loading = ref(false)
  const error   = ref(null)

  // ── Getters ──────────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => profile.value?.role === 'admin')
  const userName = computed(() =>
    profile.value?.full_name || profile.value?.email || 'User'
  )

  // ── Helpers ───────────────────────────────────────────────────────────────

  /**
   * Extract a human-readable error message from an Axios error.
   * Handles both:
   *   - FastAPI 400 → { detail: "string message" }
   *   - FastAPI 422 → { detail: [{ msg: "...", loc: [...] }] }
   */
  function _extractError(err, fallback = 'Đã xảy ra lỗi.') {
    const detail = err.response?.data?.detail
    if (!detail) return fallback
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      // Map Pydantic error locs to readable field names
      const fieldMap = { password: 'Mật khẩu', email: 'Email', full_name: 'Họ tên' }
      return detail.map((d) => {
        const field = fieldMap[d.loc?.[d.loc.length - 1]] || ''
        const msg = d.msg || ''
        // Clean up pydantic messages
        const clean = msg
          .replace('String should have at least', 'Tối thiểu')
          .replace('characters', 'ký tự')
          .replace('Value error,', '')
          .trim()
        return field ? `${field}: ${clean}` : clean
      }).join(' | ')
    }
    return fallback
  }

  function setTokens(accessToken) {
    token.value = accessToken
    setClientTokens(accessToken)
  }

  function clearAuth() {
    token.value   = null
    profile.value = null
    clearTokens()
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  /**
   * Register a new user.
   * Returns { needsVerification: true, email } if email OTP is required.
   * Returns true on unexpected auto-login (future-proof).
   */
  async function register(email, password, fullName) {
    loading.value = true
    error.value   = null
    try {
      const data = await authService.register({
        email,
        password,
        full_name: fullName,
      })
      // Backend now returns { needs_verification, email } — no token yet.
      if (data.needs_verification) {
        return { needsVerification: true, email: data.email }
      }
      // Fallback: if backend ever returns a token directly
      if (data.access_token) {
        setTokens(data.access_token)
        await fetchProfile()
      }
      return true
    } catch (err) {
      error.value = _extractError(err, 'Đăng ký thất bại.')
      return false
    } finally {
      loading.value = false
    }
  }

  /** Verify email OTP and auto-login on success. */
  async function verifyEmail(email, code) {
    loading.value = true
    error.value   = null
    try {
      const data = await authService.verifyEmail(email, code)
      setTokens(data.access_token)
      await fetchProfile()
      return true
    } catch (err) {
      error.value = _extractError(err, 'Mã xác minh không đúng.')
      return false
    } finally {
      loading.value = false
    }
  }

  /** Re-send the email verification OTP. */
  async function resendVerification(email) {
    return authService.resendVerification(email)
  }

  /** Authenticate with Google OAuth authorization code. */
  async function googleAuth(code, redirectUri) {
    loading.value = true
    error.value   = null
    try {
      const data = await authService.googleAuth(code, redirectUri)
      setTokens(data.access_token)
      await fetchProfile()
      return true
    } catch (err) {
      error.value = _extractError(err, 'Đăng nhập Google thất bại.')
      return false
    } finally {
      loading.value = false
    }
  }

  /** Log in with email + password. */
  async function login(email, password) {
    loading.value = true
    error.value   = null
    try {
      const data = await authService.login({ email, password })
      setTokens(data.access_token)
      await fetchProfile()
      return true
    } catch (err) {
      const detail = err.response?.data?.detail || ''
      if (detail === 'email_not_verified') {
        return 'not_verified'
      }
      error.value = _extractError(err, 'Sai email hoặc mật khẩu.')
      return false
    } finally {
      loading.value = false
    }
  }

  /** Log out — revoke refresh cookie server-side when possible. */
  async function logout() {
    try {
      await authService.logout()
    } catch {
      /* ignore network errors on logout */
    }
    clearAuth()
  }

  /** Fetch current user profile from the API. */
  async function fetchProfile() {
    try {
      profile.value = await authService.getProfile()
    } catch {
      // Profile fetch failure is non-fatal during login
    }
  }

  /**
   * Called by the router guard on every navigation.
   * - If we already have a token (sessionStorage survived reload) → still need
   *   to ensure profile is loaded (it's in-memory only).
   * - If no token → try the httpOnly refresh cookie → get a new access token.
   */
  async function refreshSession() {
    if (token.value) {
      // Token exists (e.g. after a same-tab reload from sessionStorage).
      // Profile is in-memory only → re-fetch it if missing.
      if (!profile.value) {
        await fetchProfile()
      }
      return true
    }
    // No token in memory/sessionStorage → use httpOnly refresh cookie.
    try {
      const data = await authService.refresh()
      setTokens(data.access_token)
      await fetchProfile()
      return true
    } catch {
      clearAuth()
      return false
    }
  }

  /**
   * Gọi activity ping — cập nhật streak khi user mở app.
   * Gọi sau khi fetchProfile() để đảm bảo profile đã load.
   */
  async function activityPing() {
    try {
      const data = await authService.activityPing()
      // Cập nhật streak trong profile nếu thay đổi
      if (profile.value && data.streak !== undefined) {
        profile.value = { ...profile.value, streak: data.streak }
      }
      return data
    } catch {
      // Activity ping failure là non-fatal
    }
  }

  /** Upload avatar và refresh profile */
  async function uploadAvatar(file) {
    loading.value = true
    error.value = null
    try {
      await authService.uploadAvatar(file)
      await fetchProfile()
      return true
    } catch (err) {
      error.value = _extractError(err, 'Upload thất bại.')
      return false
    } finally {
      loading.value = false
    }
  }

  /** Update profile fields. */
  async function updateProfile(payload) {
    loading.value = true
    error.value   = null
    try {
      profile.value = await authService.updateProfile(payload)
      return true
    } catch (err) {
      error.value = _extractError(err, 'Cập nhật thất bại.')
      return false
    } finally {
      loading.value = false
    }
  }

  async function changePassword(currentPassword, newPassword) {
    loading.value = true
    error.value = null
    try {
      await authService.changePassword(currentPassword, newPassword)
      return true
    } catch (err) {
      error.value = _extractError(err, 'Đổi mật khẩu thất bại.')
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    token, profile, loading, error,
    isAuthenticated, isAdmin, userName,
    register, login, logout, fetchProfile, refreshSession, updateProfile, activityPing, uploadAvatar,
    changePassword, verifyEmail, resendVerification, googleAuth,
  }
})

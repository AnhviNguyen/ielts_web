/**
 * src/stores/auth.js
 * ───────────────────
 * Pinia store for authentication state.
 * Handles login, register, logout, profile fetch, and token persistence.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/authService.js'

export const useAuthStore = defineStore('auth', () => {
  // ── State ────────────────────────────────────────────────────────────────
  const token   = ref(localStorage.getItem('access_token') || localStorage.getItem('token') || null)
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
  function setTokens(accessToken, refreshToken) {
    token.value = accessToken
    localStorage.setItem('access_token', accessToken)
    localStorage.removeItem('token')
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    } else {
      localStorage.removeItem('refresh_token')
    }
  }

  function clearAuth() {
    token.value   = null
    profile.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  /** Register a new user account and auto-login. */
  async function register(email, password, fullName) {
    loading.value = true
    error.value   = null
    try {
      const data = await authService.register({
        email,
        password,
        full_name: fullName,
      })
      setTokens(data.access_token, data.refresh_token)
      await fetchProfile()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Registration failed'
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
      setTokens(data.access_token, data.refresh_token)
      await fetchProfile()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Invalid email or password'
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
      error.value = err.response?.data?.detail || 'Upload thất bại'
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
      error.value = err.response?.data?.detail || 'Update failed'
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
      error.value = err.response?.data?.detail || 'Đổi mật khẩu thất bại'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    token, profile, loading, error,
    isAuthenticated, isAdmin, userName,
    register, login, logout, fetchProfile, updateProfile, activityPing, uploadAvatar,
    changePassword,
  }
})

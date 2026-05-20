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
  const token   = ref(localStorage.getItem('token') || null)
  const profile = ref(null)
  const loading = ref(false)
  const error   = ref(null)

  // ── Getters ──────────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!token.value)
  const userName = computed(() =>
    profile.value?.full_name || profile.value?.email || 'User'
  )

  // ── Helpers ───────────────────────────────────────────────────────────────
  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function clearAuth() {
    token.value   = null
    profile.value = null
    localStorage.removeItem('token')
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
      setToken(data.access_token)
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
      setToken(data.access_token)
      await fetchProfile()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Invalid email or password'
      return false
    } finally {
      loading.value = false
    }
  }

  /** Clear token and profile — triggers redirect via router guard. */
  function logout() {
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

  return {
    token, profile, loading, error,
    isAuthenticated, userName,
    register, login, logout, fetchProfile, updateProfile, activityPing, uploadAvatar,
  }
})

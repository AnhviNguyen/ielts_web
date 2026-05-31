import apiClient from '@/api/client.js'

export class AuthService {
  async register(payload) {
    const { data } = await apiClient.post('/auth/register', payload)
    return data
  }

  async verifyEmail(email, code) {
    const { data } = await apiClient.post('/auth/verify-email', { email, code })
    return data
  }

  async resendVerification(email) {
    const { data } = await apiClient.post('/auth/resend-verification', { email })
    return data
  }

  async googleAuth(code, redirectUri) {
    const { data } = await apiClient.post('/auth/google', { code, redirect_uri: redirectUri })
    return data
  }

  async login(payload) {
    const { data } = await apiClient.post('/auth/login', payload)
    return data
  }

  async refresh() {
    const { data } = await apiClient.post('/auth/refresh', {})
    return data
  }

  async getProfile() {
    const { data } = await apiClient.get('/users/me')
    return data
  }

  async updateProfile(payload) {
    const { data } = await apiClient.patch('/users/me', payload)
    return data
  }

  /** Upload avatar — multipart form */
  async uploadAvatar(file) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.put('/users/me/avatar', form)
    return data
  }

  /** Ping activity để cập nhật streak khi user mở app */
  async activityPing() {
    const { data } = await apiClient.post('/users/me/activity-ping')
    return data
  }

  async changePassword(currentPassword, newPassword) {
    const { data } = await apiClient.post('/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return data
  }

  async forgotPassword(email) {
    const { data } = await apiClient.post('/auth/forgot-password', { email })
    return data
  }

  async resetPassword(token, newPassword) {
    const { data } = await apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    })
    return data
  }

  async logout() {
    const { data } = await apiClient.post('/auth/logout', {})
    return data
  }
}

export const authService = new AuthService()

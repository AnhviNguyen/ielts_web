import apiClient from '@/api/client.js'

export class AuthService {
  async register(payload) {
    const { data } = await apiClient.post('/auth/register', payload)
    return data
  }

  async login(payload) {
    const { data } = await apiClient.post('/auth/login', payload)
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
    const { data } = await apiClient.put('/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  }

  /** Ping activity để cập nhật streak khi user mở app */
  async activityPing() {
    const { data } = await apiClient.post('/users/me/activity-ping')
    return data
  }
}

export const authService = new AuthService()

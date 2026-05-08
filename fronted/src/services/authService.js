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
    const { data } = await apiClient.get('/user/profile')
    return data
  }

  async updateProfile(payload) {
    const { data } = await apiClient.put('/user/profile', payload)
    return data
  }
}

export const authService = new AuthService()

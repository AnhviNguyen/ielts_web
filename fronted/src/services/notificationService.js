import apiClient from '@/api/client.js'

export async function fetchNotifications(limit = 30) {
  const { data } = await apiClient.get('/users/me/notifications', { params: { limit } })
  return data
}

export async function markNotificationRead(id) {
  const { data } = await apiClient.patch(`/users/me/notifications/${id}/read`)
  return data
}

export async function markAllNotificationsRead() {
  const { data } = await apiClient.post('/users/me/notifications/read-all')
  return data
}

export async function getNotificationSettings() {
  const { data } = await apiClient.get('/users/me/notifications/settings')
  return data
}

export async function updateNotificationSettings(body) {
  const { data } = await apiClient.post('/users/me/notifications/settings', body)
  return data
}

export async function fetchNextStudyTask() {
  const { data } = await apiClient.get('/users/me/study-plan/next-task')
  return data
}

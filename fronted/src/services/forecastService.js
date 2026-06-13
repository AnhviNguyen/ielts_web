import apiClient from '@/api/client.js'

export async function fetchForecast(skill = 'overall') {
  const { data } = await apiClient.get(`/users/me/forecast/${encodeURIComponent(skill)}`)
  return data
}

export async function fetchForecastAlerts() {
  const { data } = await apiClient.get('/users/me/forecast/alerts')
  return data
}

export async function fetchNextWeekForecast(notify = true) {
  const { data } = await apiClient.get('/users/me/forecast/next-week', {
    params: { notify },
  })
  return data
}

/**
 * Shadowing API — YouTube transcript pipeline.
 */
import apiClient from '@/api/client.js'
import { pollTaskResult } from '@/utils/taskPolling.js'

export function processVideo(url, { level = 'Intermediate', translate = true } = {}) {
  return apiClient
    .post('/shadowing/video/process', { url, level, translate }, { timeout: 300000 })
    .then(async ({ data }) => {
      if (data.task_id) {
        return pollTaskResult(`/shadowing/video/process/result/${data.task_id}`, {
          timeoutMs: 300000,
        })
      }
      return data
    })
}

export function getVideo(videoId) {
  return apiClient.get(`/shadowing/video/${videoId}`).then((r) => r.data)
}

export function getShadowingHistory(limit = 30) {
  return apiClient
    .get('/shadowing/history', { params: { limit } })
    .then((r) => r.data.items || [])
}

export function touchShadowingHistory(videoId) {
  return apiClient.post(`/shadowing/history/${videoId}/touch`).catch(() => {})
}

export function updateShadowingHistory(videoId, { title, level } = {}) {
  return apiClient
    .patch(`/shadowing/history/${videoId}`, { title, level })
    .then((r) => r.data)
}

export function deleteShadowingHistory(videoId) {
  return apiClient.delete(`/shadowing/history/${videoId}`).then((r) => r.data)
}

export function translateText(text, from_lang = 'en', to_lang = 'vi') {
  return apiClient
    .post('/shadowing/translate', { text, from_lang, to_lang })
    .then((r) => r.data.translation)
}

export function checkPronunciation(audioBlob, targetText) {
  const fd = new FormData()
  fd.append('file', audioBlob, 'recording.webm')
  fd.append('target_text', targetText)
  return apiClient
    .post('/shadowing/pronunciation/check', fd, {
      timeout: 120000,
      transformRequest: [
        (data, headers) => {
          delete headers['Content-Type']
          delete headers['content-type']
          return data
        },
      ],
    })
    .then((r) => r.data)
}

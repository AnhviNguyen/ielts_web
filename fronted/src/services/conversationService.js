/**
 * conversationService.js — AI role-play conversation practice API
 */
import axios from 'axios'
import api from '@/api/client.js'
import { getAccessToken } from '@/api/tokenStore.js'

function getCsrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

const longApi = axios.create({
  baseURL: '/api',
  timeout: 90000,
  withCredentials: true,
})

longApi.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  const method = (config.method || 'get').toLowerCase()
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrf = getCsrfToken()
    if (csrf) config.headers['X-CSRF-Token'] = csrf
  }
  return config
})

export async function fetchTopics(level = null) {
  const params = level ? { level } : {}
  const { data } = await api.get('/conversation/topics', { params })
  return data.data
}

export async function startConversation(topicId) {
  const { data } = await longApi.post('/conversation/start', { topic_id: topicId })
  return data.data
}

export async function sendTurn(sessionId, message) {
  const { data } = await longApi.post('/conversation/turn', {
    session_id: sessionId,
    message,
  })
  return data.data
}

export async function sendVoiceTurn(sessionId, audioBlob, filename = 'recording.webm') {
  const form = new FormData()
  form.append('session_id', String(sessionId))
  form.append('audio', audioBlob, filename)
  const { data } = await longApi.post('/conversation/turn/voice', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data.data
}

export async function endConversation(sessionId) {
  const { data } = await longApi.post('/conversation/end', { session_id: sessionId })
  return data.data
}

export async function fetchReplyHint(sessionId, aiMessage) {
  const { data } = await api.post('/conversation/assist/hint', {
    session_id: sessionId,
    ai_message: aiMessage,
  })
  return data.data
}

export async function translateAiMessage(text) {
  const { data } = await api.post('/conversation/assist/translate', { text })
  return data.data
}

export const LEVEL_LABELS = {
  beginner: { label: 'Beginner', color: 'emerald' },
  intermediate: { label: 'Intermediate', color: 'blue' },
  advanced: { label: 'Advanced', color: 'purple' },
}

import apiClient from '@/api/client.js'

export async function fetchWritingTopic(topicId) {
  const { data } = await apiClient.get(`/writing/topics/${topicId}`)
  return data?.data ?? data
}

export async function listWritingSets() {
  const { data } = await apiClient.get('/writing/sets')
  return data?.data ?? { items: [], total: 0 }
}

export async function fetchWritingSetByTopic(topicId) {
  const { data } = await apiClient.get(`/writing/sets/by-topic/${topicId}`)
  return data?.data ?? data
}

export async function postWritingChat({ prompt_text, user_message, history }) {
  const { data } = await apiClient.post('/writing/chat', {
    prompt_text: prompt_text || '',
    user_message,
    history: history || [],
  })
  return data
}

/**
 * Submit essay for AI evaluation + history.
 * @returns {Promise<{ history_id, band_score, xp_earned, evaluation, message }>}
 */
export async function submitWriting(payload) {
  const { data } = await apiClient.post('/writing/submit', payload, { timeout: 120_000 })
  return data
}

export async function fetchWritingResult(historyId) {
  const { data } = await apiClient.get(`/writing/result/${historyId}`)
  return data
}

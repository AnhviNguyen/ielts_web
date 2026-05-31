/**
 * translationService.js
 * API client for Translation Practice feature.
 */
import api from '@/api/client.js'

export async function fetchSteps() {
  const { data } = await api.get('/translation/steps')
  return data.data
}

export async function fetchTopics(stepId) {
  const { data } = await api.get(`/translation/steps/${stepId}/topics`)
  return data.data
}

export async function fetchSentences(topicId) {
  const { data } = await api.get(`/translation/topics/${topicId}/sentences`)
  return data.data
}

export async function checkTranslation(sentenceId, userTranslation) {
  const { data } = await api.post('/translation/check', {
    sentence_id: sentenceId,
    user_translation: userTranslation,
  })
  return data.data
}

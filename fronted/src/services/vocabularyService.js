/**
 * vocabularyService.js
 * ─────────────────────
 * API layer for Vocabulary topics, words, search and annotations.
 *
 * Uses the shared apiClient (with JWT interceptor) instead of a raw axios
 * instance so authentication is handled consistently across the app.
 */
import apiClient from '@/api/client.js'

// ═══ Topics ════════════════════════════════════════════════════════════════

let _topicsCache = null
let _topicsCacheAt = 0
const TOPICS_CACHE_MS = 5 * 60 * 1000

/** @returns {Promise<VocabTopicResponse[]>} */
export const getTopics = (opts = {}) => {
  const force = opts.force === true
  const now = Date.now()
  if (!force && _topicsCache && now - _topicsCacheAt < TOPICS_CACHE_MS) {
    return Promise.resolve(_topicsCache)
  }
  return apiClient.get('/vocabulary/topics').then((r) => {
    _topicsCache = r.data
    _topicsCacheAt = Date.now()
    return r.data
  })
}

export function invalidateTopicsCache() {
  _topicsCache = null
  _topicsCacheAt = 0
}

/** @param {number} topicId @returns {Promise<{ topic, words }>} */
export const getTopicDetail = (topicId) =>
  apiClient.get(`/vocabulary/topics/${topicId}`).then(r => r.data)

/** @returns {Promise<{ created, topics_created, words_created, message }>} */
export const bootstrapVocabulary = () =>
  apiClient.post('/vocabulary/bootstrap').then(r => r.data)

/** @param {string} name @returns {Promise<VocabTopicResponse>} */
export const createTopic = (name) =>
  apiClient.post('/vocabulary/topics', { name }).then((r) => {
    invalidateTopicsCache()
    return r.data
  })

/** @param {number} id @param {{ name?: string, sort_order?: number }} body */
export const updateTopic = (id, body) =>
  apiClient.patch(`/vocabulary/topics/${id}`, body).then(r => r.data)

/** @param {number} id */
export const deleteTopic = (id) =>
  apiClient.delete(`/vocabulary/topics/${id}`).then((r) => {
    invalidateTopicsCache()
    return r
  })

// ═══ Words ════════════════════════════════════════════════════════════════

/** @returns {Promise<VocabWordResponse[]>} */
export const getWords = (topicId) =>
  apiClient.get(`/vocabulary/topics/${topicId}/words`).then(r => r.data)

/**
 * Save a new word into a topic.
 * @param {number} topicId
 * @param {object} wordData — word, phonetic, word_type, meaning_vi, example, note,
 *                            source_quiz_id?, source_type? ('reading'|'listening'|'manual')
 * @returns {Promise<VocabWordResponse>}
 */
export const saveWord = (topicId, wordData) =>
  apiClient.post(`/vocabulary/topics/${topicId}/words`, wordData).then(r => r.data)

/** @param {number} topicId @param {number} wordId @param {object} body */
export const updateWord = (topicId, wordId, body) =>
  apiClient.patch(`/vocabulary/topics/${topicId}/words/${wordId}`, body).then(r => r.data)

/** @param {number} topicId @param {number} wordId */
export const deleteWord = (topicId, wordId) =>
  apiClient.delete(`/vocabulary/topics/${topicId}/words/${wordId}`)

// ═══ Search & Stats ═══════════════════════════════════════════════════════

/**
 * Full-text search across ALL user topics.
 * @param {string} query
 * @returns {Promise<VocabWordResponse[]>}
 */
export const searchWords = (query) =>
  apiClient.get('/vocabulary/words/search', { params: { q: query } }).then(r => r.data)

/**
 * Aggregate word counts per mastery level across all topics.
 * @returns {Promise<{ total: number, new: number, learning: number, mastered: number }>}
 */
export const getVocabStats = () =>
  apiClient.get('/vocabulary/stats').then(r => r.data)

/** @param {{ topic_id: number, duration_seconds: number, words_reviewed: number }} body */
export const completeVocabSession = (body) =>
  apiClient.post('/vocabulary/sessions/complete', body).then(r => r.data)

/** @returns {Promise<{ modes: Array<{ id, label, description }> }>} */
export const getStudyModes = () =>
  apiClient.get('/vocabulary/study-modes').then(r => r.data)

export const getStudyQueue = (topicId) =>
  apiClient.get(`/vocabulary/topics/${topicId}/study-queue`).then(r => r.data)

export const recordReview = (topicId, wordId, quality) =>
  apiClient.post(`/vocabulary/topics/${topicId}/words/${wordId}/review`, { quality }).then(r => r.data)

export const getMcqOptions = (topicId, wordId) =>
  apiClient.get(`/vocabulary/topics/${topicId}/words/${wordId}/mcq`).then(r => r.data)

export const generateReadingPassage = (topicId, wordIds) =>
  apiClient
    .post(`/vocabulary/topics/${topicId}/reading-passage`, { word_ids: wordIds })
    .then(r => r.data)

// ═══ Reading Annotations ══════════════════════════════════════════════════

export const getAnnotation = (sessionId) =>
  apiClient.get(`/annotations/${sessionId}`).then(r => r.data)

export const saveAnnotation = (sessionId, body) =>
  apiClient.put(`/annotations/${sessionId}`, body).then(r => r.data)

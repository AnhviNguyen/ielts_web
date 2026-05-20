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

/** @returns {Promise<VocabTopicResponse[]>} */
export const getTopics = () =>
  apiClient.get('/vocabulary/topics').then(r => r.data)

/** @param {string} name @returns {Promise<VocabTopicResponse>} */
export const createTopic = (name) =>
  apiClient.post('/vocabulary/topics', { name }).then(r => r.data)

/** @param {number} id @param {{ name?: string, sort_order?: number }} body */
export const updateTopic = (id, body) =>
  apiClient.patch(`/vocabulary/topics/${id}`, body).then(r => r.data)

/** @param {number} id */
export const deleteTopic = (id) =>
  apiClient.delete(`/vocabulary/topics/${id}`)

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

// ═══ Reading Annotations ══════════════════════════════════════════════════

export const getAnnotation = (sessionId) =>
  apiClient.get(`/annotations/${sessionId}`).then(r => r.data)

export const saveAnnotation = (sessionId, body) =>
  apiClient.put(`/annotations/${sessionId}`, body).then(r => r.data)

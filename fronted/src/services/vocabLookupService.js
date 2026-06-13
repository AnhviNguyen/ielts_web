/**
 * Vocabulary lookup via backend proxy to dictionaryapi.dev.
 */
import apiClient from '@/api/client.js'

/**
 * @param {string} word
 * @returns {Promise<object>}
 */
export async function fetchLookupWord(word) {
  const { data } = await apiClient.get('/vocabulary/lookup', {
    params: { word },
  })
  return data
}

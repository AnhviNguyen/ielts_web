/**
 * Word-level phoneme pronunciation API (Wav2Vec2 + CMU).
 */
import apiClient from '@/api/client.js'

export function getWordExpectedPhonemes(word) {
  return apiClient
    .get(`/pronunciation/word/${encodeURIComponent(word)}/expected`)
    .then((r) => r.data)
}

export function scoreWordPronunciation(word, audioBlob) {
  const fd = new FormData()
  fd.append('word', word)
  fd.append('audio', audioBlob, 'recording.webm')
  return apiClient
    .post('/pronunciation/word', fd, {
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

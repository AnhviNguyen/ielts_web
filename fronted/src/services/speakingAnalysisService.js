import apiClient from '@/api/client.js'

let _cacheKey = ''
let _cachePromise = null

/**
 * One OpenRouter-backed call (via backend) for grammar + vocabulary card data.
 * @param {{ transcript: string, questionText?: string }} params
 */
export async function fetchLanguageAnalysis({ transcript, questionText = '' }) {
  const key = `${transcript}::${questionText}`
  if (_cacheKey === key && _cachePromise) return _cachePromise

  _cacheKey = key
  _cachePromise = apiClient
    .post(
      '/speaking/analyze-language',
      {
        transcript,
        question_text: questionText,
      },
      { timeout: 90_000 },
    )
    .then((res) => res.data)
    .catch((err) => {
      _cacheKey = ''
      _cachePromise = null
      throw err
    })

  return _cachePromise
}

export function clearLanguageAnalysisCache() {
  _cacheKey = ''
  _cachePromise = null
}

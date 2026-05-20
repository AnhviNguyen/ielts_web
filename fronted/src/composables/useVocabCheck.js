import { ref, computed, watch } from 'vue'
import { fetchLanguageAnalysis, clearLanguageAnalysisCache } from '@/services/speakingAnalysisService.js'
import { highlightTranscript } from '@/utils/highlightTranscript.js'

/**
 * Vocabulary analysis from Whisper transcript via backend OpenRouter proxy.
 * @param {{ transcript: import('vue').Ref<string>|string, questionText?: import('vue').Ref<string>|string, auto?: boolean }} options
 */
export function useVocabCheck(options = {}) {
  const loading = ref(false)
  const error = ref(null)
  const score = ref(0)
  const weakWords = ref([])
  const strongWords = ref([])
  const replacements = ref([])
  const llmGenerated = ref(false)

  const transcriptRef = options.transcript
  const questionRef = options.questionText
  const auto = options.auto !== false

  function _val(maybeRef, fallback = '') {
    if (maybeRef && typeof maybeRef === 'object' && 'value' in maybeRef) return maybeRef.value || fallback
    return maybeRef || fallback
  }

  function applyVocabPayload(payload = {}) {
    const va = payload.vocabulary_analysis || payload.vocabulary || {}
    score.value = Number(va.score ?? payload.vocabulary_score ?? 0)
    llmGenerated.value = Boolean(payload.llm_generated ?? va.llm_generated ?? false)

    weakWords.value = (va.weak_words || []).map((w) => ({
      text: w.text || w.word_used || w.word || '',
      reason: w.reason || '',
    }))
    strongWords.value = (va.strong_words || []).map((w) => ({
      text: w.text || w.word || '',
      reason: w.reason || '',
    }))

    const reps = va.replacements || va.feedback || payload.vocabulary_feedback || []
    replacements.value = reps.map((r) => ({
      weak: r.weak || r.word_used || r.text || '',
      better: r.better || r.better_alternative || '',
      reason: r.reason || '',
    }))
  }

  const highlightedHtml = computed(() => {
    const transcript = _val(transcriptRef, '')
    const spans = [
      ...weakWords.value.map((w) => ({
        text: w.text,
        className: 'hl-vocab-weak',
        title: w.reason || 'weak / repetitive',
      })),
      ...strongWords.value.map((w) => ({
        text: w.text,
        className: 'hl-vocab-strong',
        title: w.reason || 'strong usage',
      })),
    ]
    return highlightTranscript(transcript, spans)
  })

  async function analyze(transcript, questionText = '') {
    const t = transcript ?? _val(transcriptRef, '')
    const q = questionText ?? _val(questionRef, '')
    if (!t.trim()) {
      error.value = 'No transcript to analyze.'
      return null
    }

    loading.value = true
    error.value = null
    try {
      const data = await fetchLanguageAnalysis({ transcript: t, questionText: q })
      applyVocabPayload(data)
      return data.vocabulary_analysis || data
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.message ||
        'Vocabulary analysis failed.'
      error.value = msg
      return null
    } finally {
      loading.value = false
    }
  }

  function hydrateFromEvaluate(result) {
    if (!result) return
    applyVocabPayload({
      vocabulary_analysis: result.vocabulary_analysis,
      vocabulary_feedback: result.vocabulary?.feedback,
      vocabulary_score: result.vocabulary?.score ?? result.lexical_resource_score,
      llm_generated: result.llm_generated,
    })
    llmGenerated.value = Boolean(result.llm_generated)
  }

  if (auto && transcriptRef && typeof transcriptRef === 'object' && 'value' in transcriptRef) {
    watch(
      () => [_val(transcriptRef), _val(questionRef)],
      ([t]) => {
        if (
          t &&
          t.trim().length > 8 &&
          !llmGenerated.value &&
          !weakWords.value.length &&
          !strongWords.value.length
        ) {
          analyze(t, _val(questionRef))
        }
      },
      { immediate: false },
    )
  }

  return {
    loading,
    error,
    score,
    weakWords,
    strongWords,
    replacements,
    highlightedHtml,
    llmGenerated,
    analyze,
    hydrateFromEvaluate,
    clearCache: clearLanguageAnalysisCache,
  }
}

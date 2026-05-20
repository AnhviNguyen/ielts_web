import { ref, computed, watch } from 'vue'
import { fetchLanguageAnalysis, clearLanguageAnalysisCache } from '@/services/speakingAnalysisService.js'
import { highlightTranscript } from '@/utils/highlightTranscript.js'

/**
 * Grammar analysis from Whisper transcript via backend OpenRouter proxy.
 * @param {{ transcript: import('vue').Ref<string>|string, questionText?: import('vue').Ref<string>|string, auto?: boolean }} options
 */
export function useGrammarCheck(options = {}) {
  const loading = ref(false)
  const error = ref(null)
  const score = ref(0)
  const errors = ref([])
  const llmGenerated = ref(false)

  const transcriptRef = options.transcript
  const questionRef = options.questionText
  const auto = options.auto !== false

  function _val(maybeRef, fallback = '') {
    if (maybeRef && typeof maybeRef === 'object' && 'value' in maybeRef) return maybeRef.value || fallback
    return maybeRef || fallback
  }

  function applyGrammarPayload(payload = {}) {
    const ga = payload.grammar_analysis || payload.grammar || {}
    score.value = Number(ga.score ?? payload.grammar_score ?? 0)
    llmGenerated.value = Boolean(payload.llm_generated ?? ga.llm_generated ?? false)

    const list = ga.errors || payload.grammar_errors || []
    errors.value = list.map((e) => ({
      text: e.text || e.original || '',
      error_type: e.error_type || e.type || 'grammar',
      correction: e.correction || '',
      explanation: e.explanation || '',
    }))
  }

  const highlightedHtml = computed(() => {
    const transcript = _val(transcriptRef, '')
    const spans = errors.value
      .filter((e) => e.text)
      .map((e) => ({
        text: e.text,
        className: 'hl-grammar-error',
        title: e.error_type,
      }))
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
      applyGrammarPayload(data)
      return data.grammar_analysis || data
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.message ||
        'Grammar analysis failed.'
      error.value = msg
      return null
    } finally {
      loading.value = false
    }
  }

  function hydrateFromEvaluate(result) {
    if (!result) return
    applyGrammarPayload({
      grammar_analysis: result.grammar_analysis,
      grammar_errors: result.grammar?.errors,
      grammar_score: result.grammar?.score ?? result.grammar_range_accuracy_score,
      llm_generated: result.llm_generated,
    })
    llmGenerated.value = Boolean(result.llm_generated)
  }

  if (auto && transcriptRef && typeof transcriptRef === 'object' && 'value' in transcriptRef) {
    watch(
      () => [_val(transcriptRef), _val(questionRef)],
      ([t]) => {
        if (t && t.trim().length > 8 && !llmGenerated.value && !errors.value.length) {
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
    errors,
    highlightedHtml,
    llmGenerated,
    analyze,
    hydrateFromEvaluate,
    clearCache: clearLanguageAnalysisCache,
  }
}

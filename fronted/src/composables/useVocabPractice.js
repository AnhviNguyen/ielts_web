import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStudyQueue, recordReview, generateReadingPassage, completeVocabSession } from '@/services/vocabularyService.js'
import { useAuthStore } from '@/stores/auth.js'
import { VOCAB_PRACTICE_MODE_IDS } from '@/constants/vocabPracticeModes.js'
import { normalizeVocabAnswer } from '@/utils/vocabAnswer.js'
import { speakEnglish } from '@/utils/vocabSpeech.js'

const READING_BATCH = 5

export function useVocabPractice() {
  const route = useRoute()
  const router = useRouter()
  const auth = useAuthStore()

  const sessionStartedAt = ref(Date.now())
  const sessionReported = ref(false)
  const sessionXpEarned = ref(null)

  const topicId = computed(() => Number(route.params.topicId))
  const currentMode = computed(() => {
    const m = route.query.mode || 'flashcard'
    return VOCAB_PRACTICE_MODE_IDS.includes(m) ? m : 'flashcard'
  })

  const loading = ref(true)
  const loadError = ref('')
  const topicName = ref('')
  const dueCount = ref(null)
  const queue = ref([])
  const queueIndex = ref(0)
  const doneCount = ref(0)
  const correctCount = ref(0)
  const completed = ref(false)
  const reviewing = ref(false)

  const cardFlipped = ref(false)
  const typingInput = ref('')
  const typingResult = ref(null)
  const typingStageRef = ref(null)
  const dictationStageRef = ref(null)

  const readingPassage = ref(null)
  const readingLoading = ref(false)
  const readingError = ref('')
  const readingBatchWordIds = ref([])
  const gapAnswers = ref({})
  const gapStatus = ref({})
  const readingChecked = ref(false)
  const readingAllCorrect = ref(false)

  const currentWord = computed(() =>
    currentMode.value === 'reading' ? null : (queue.value[queueIndex.value] ?? null)
  )

  const cardLabel = computed(() => {
    if (!queue.value.length) return '0 / 0'
    if (currentMode.value === 'reading' && readingBatchWordIds.value.length) {
      const end = Math.min(queueIndex.value + readingBatchWordIds.value.length, queue.value.length)
      return `${queueIndex.value + 1}–${end} / ${queue.value.length}`
    }
    return `${queueIndex.value + 1} / ${queue.value.length}`
  })

  const progressPct = computed(() =>
    queue.value.length ? Math.round((doneCount.value / queue.value.length) * 100) : 0
  )

  const showFooter = computed(
    () => !loading.value && !completed.value && queue.value.length && currentMode.value !== 'reading'
  )

  function setMode(id) {
    if (id === currentMode.value) return
    router.replace({ query: { ...route.query, mode: id } })
  }

  async function reportSessionIfNeeded() {
    if (sessionReported.value || doneCount.value < 1) return
    sessionReported.value = true
    const duration_seconds = Math.max(
      1,
      Math.round((Date.now() - sessionStartedAt.value) / 1000)
    )
    try {
      const res = await completeVocabSession({
        topic_id: topicId.value,
        duration_seconds,
        words_reviewed: doneCount.value,
      })
      sessionXpEarned.value = res.xp_earned
      if (auth.profile) auth.profile.xp = res.total_xp
      await auth.fetchProfile()
    } catch {
      sessionReported.value = false
    }
  }

  async function goBack() {
    await reportSessionIfNeeded()
    router.push('/vocabulary')
  }

  async function loadQueue() {
    loading.value = true
    loadError.value = ''
    try {
      const data = await getStudyQueue(topicId.value)
      topicName.value = data.topic?.name || ''
      dueCount.value = data.due_count
      queue.value = data.words || []
      restartSession()
    } catch (e) {
      loadError.value = e?.response?.data?.detail || 'Không tải được hàng đợi.'
    } finally {
      loading.value = false
    }
  }

  function restartSession() {
    queueIndex.value = 0
    doneCount.value = 0
    correctCount.value = 0
    completed.value = false
    sessionStartedAt.value = Date.now()
    sessionReported.value = false
    sessionXpEarned.value = null
    resetCardState()
    onModeChange()
  }

  function resetCardState() {
    cardFlipped.value = false
    typingInput.value = ''
    typingResult.value = null
    readingChecked.value = false
    readingAllCorrect.value = false
    gapAnswers.value = {}
    gapStatus.value = {}
  }

  function onModeChange() {
    resetCardState()
    if (currentMode.value === 'reading') {
      loadReadingPassage()
      return
    }
    const w = currentWord.value
    if (!w) return
    nextTick(() => {
      if (currentMode.value === 'dictation') {
        dictationStageRef.value?.focus()
        speakEnglish(w.example || w.word)
      } else if (currentMode.value === 'typing') {
        typingStageRef.value?.focus()
        speakEnglish(w.word)
      } else if (currentMode.value === 'flashcard') {
        speakEnglish(w.word)
      }
    })
  }

  function readingBatchWords() {
    return queue.value.slice(queueIndex.value, queueIndex.value + READING_BATCH)
  }

  async function loadReadingPassage() {
    const batch = readingBatchWords()
    if (!batch.length) return
    readingLoading.value = true
    readingError.value = ''
    readingPassage.value = null
    try {
      const ids = batch.map((w) => w.id)
      const data = await generateReadingPassage(topicId.value, ids)
      readingPassage.value = data
      readingBatchWordIds.value = data.word_ids?.length ? data.word_ids : ids
      const ans = {}
      for (const p of data.paragraphs || []) {
        for (const part of p.parts || []) {
          if (part.type === 'gap' && part.id) ans[part.id] = ''
        }
      }
      gapAnswers.value = ans
      gapStatus.value = {}
      readingChecked.value = false
    } catch (e) {
      readingError.value = e?.response?.data?.detail || 'Không tạo được đoạn văn.'
    } finally {
      readingLoading.value = false
    }
  }

  async function checkReadingPassage() {
    const answers = readingPassage.value?.answers || {}
    let allOk = true
    const status = {}
    for (const [gid, expected] of Object.entries(answers)) {
      const ok = normalizeVocabAnswer(gapAnswers.value[gid]) === normalizeVocabAnswer(expected)
      status[gid] = ok ? 'ok' : 'bad'
      if (!ok) allOk = false
    }
    gapStatus.value = status
    readingChecked.value = true
    readingAllCorrect.value = allOk
  }

  async function finishReadingBatch() {
    const answers = readingPassage.value?.answers || {}
    const gapKeys = Object.keys(answers)
    const idByGap = {}
    readingBatchWordIds.value.forEach((wid, i) => {
      idByGap[gapKeys[i] || `g${i}`] = wid
    })
    for (const [gid, expected] of Object.entries(answers)) {
      const wid = idByGap[gid]
      if (!wid) continue
      const ok = normalizeVocabAnswer(gapAnswers.value[gid]) === normalizeVocabAnswer(expected)
      await submitReviewById(wid, ok)
      doneCount.value++
      if (ok) correctCount.value++
    }
    const step = readingBatchWordIds.value.length || READING_BATCH
    const next = queueIndex.value + step
    if (next >= queue.value.length) {
      completed.value = true
      return
    }
    queueIndex.value = next
    resetCardState()
    loadReadingPassage()
  }

  async function submitReviewById(wordId, correct) {
    reviewing.value = true
    try {
      await recordReview(topicId.value, wordId, correct ? 5 : 2)
    } catch (e) {
      console.error(e)
    } finally {
      reviewing.value = false
    }
  }

  async function submitReview(correct) {
    const w = currentWord.value
    if (!w) return
    await submitReviewById(w.id, correct)
  }

  function speakWord(word) {
    speakEnglish(word)
  }

  function speakExample() {
    const w = currentWord.value
    speakEnglish(w?.example || w?.word)
  }

  async function markAnswer(correct) {
    correctCount.value += correct ? 1 : 0
    doneCount.value++
    await submitReview(correct)
    advanceQueue()
  }

  async function checkTypingWord() {
    const w = currentWord.value
    if (!w || typingResult.value) return
    const ok = normalizeVocabAnswer(typingInput.value) === normalizeVocabAnswer(w.word)
    typingResult.value = ok ? 'correct' : 'wrong'
    if (ok) correctCount.value++
    doneCount.value++
    await submitReview(ok)
  }

  async function checkDictation() {
    const w = currentWord.value
    if (!w || typingResult.value) return
    const ok = normalizeVocabAnswer(typingInput.value) === normalizeVocabAnswer(w.word)
    typingResult.value = ok ? 'correct' : 'wrong'
    if (ok) correctCount.value++
    doneCount.value++
    await submitReview(ok)
  }

  function nextWord() {
    advanceQueue()
  }

  async function advanceQueue() {
    const next = queueIndex.value + 1
    if (next >= queue.value.length) {
      completed.value = true
      await reportSessionIfNeeded()
      return
    }
    queueIndex.value = next
    resetCardState()
    onModeChange()
  }

  function goPrevCard() {
    if (queueIndex.value <= 0) return
    queueIndex.value--
    resetCardState()
    onModeChange()
  }

  function goNextCard() {
    if (queueIndex.value >= queue.value.length - 1) return
    queueIndex.value++
    resetCardState()
    onModeChange()
  }

  function onKeydown(e) {
    if (loading.value || completed.value) return
    if (currentMode.value !== 'flashcard' || !currentWord.value) return
    if (e.code === 'Space' || e.code === 'Enter') {
      e.preventDefault()
      if (!cardFlipped.value) cardFlipped.value = true
    }
    if (e.code === 'ArrowLeft') {
      e.preventDefault()
      goPrevCard()
    }
    if (e.code === 'ArrowRight') {
      e.preventDefault()
      goNextCard()
    }
  }

  onMounted(() => {
    loadQueue()
    window.addEventListener('keydown', onKeydown)
  })
  onUnmounted(() => {
    window.removeEventListener('keydown', onKeydown)
    reportSessionIfNeeded()
  })

  watch(() => route.params.topicId, loadQueue)
  watch(currentMode, onModeChange)
  watch(queueIndex, () => {
    if (currentMode.value === 'reading') loadReadingPassage()
  })

  return {
    currentMode,
    loading,
    loadError,
    topicName,
    dueCount,
    queue,
    queueIndex,
    doneCount,
    correctCount,
    completed,
    reviewing,
    cardFlipped,
    typingInput,
    typingResult,
    typingStageRef,
    dictationStageRef,
    readingPassage,
    readingLoading,
    readingError,
    readingBatchWordIds,
    gapAnswers,
    gapStatus,
    readingChecked,
    readingAllCorrect,
    currentWord,
    cardLabel,
    progressPct,
    showFooter,
    sessionXpEarned,
    setMode,
    goBack,
    loadQueue,
    restartSession,
    loadReadingPassage,
    checkReadingPassage,
    finishReadingBatch,
    speakWord,
    speakExample,
    markAnswer,
    checkTypingWord,
    checkDictation,
    nextWord,
    goPrevCard,
    goNextCard,
  }
}

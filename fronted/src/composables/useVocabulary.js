/**
 * useVocabulary — state & API orchestration for Vocabulary page (SRP).
 */
import { ref, computed } from 'vue'
import {
  getTopics,
  getTopicDetail,
  createTopic,
  updateTopic,
  deleteTopic,
  getWords,
  saveWord,
  updateWord,
  deleteWord as deleteWordApi,
  getVocabStats,
  getStudyModes,
} from '@/services/vocabularyService.js'
import { resolveDefaultTopicId } from '@/utils/vocabTopicPreference.js'

export function useVocabulary() {
  const topics = ref([])
  const topicsLoading = ref(false)
  const topicsError = ref('')

  const words = ref([])
  const wordsLoading = ref(false)

  const selectedTopicId = ref(null)
  const stats = ref({ total: 0, new: 0, learning: 0, mastered: 0 })
  const studyModes = ref([])

  const selectedTopic = computed(() =>
    topics.value.find((t) => t.id === selectedTopicId.value) ?? null
  )

  const canStudy = computed(() => words.value.length >= 2)

  async function refreshStats() {
    try {
      stats.value = await getVocabStats()
    } catch {
      /* informational */
    }
  }

  async function loadStudyModes() {
    try {
      const data = await getStudyModes()
      studyModes.value = data.modes || []
    } catch {
      studyModes.value = []
    }
  }

  async function loadTopics() {
    topicsLoading.value = true
    topicsError.value = ''
    try {
      topics.value = await getTopics()
    } catch {
      topicsError.value = 'Không thể kết nối đến máy chủ.'
      throw new Error(topicsError.value)
    } finally {
      topicsLoading.value = false
    }
  }

  async function selectTopic(id) {
    selectedTopicId.value = id
    wordsLoading.value = true
    try {
      const detail = await getTopicDetail(id)
      words.value = detail.words || []
      const idx = topics.value.findIndex((t) => t.id === id)
      if (idx >= 0 && detail.topic) {
        topics.value[idx] = { ...topics.value[idx], ...detail.topic }
      }
    } catch {
      words.value = await getWords(id)
    } finally {
      wordsLoading.value = false
    }
  }

  async function addTopic(name) {
    const t = await createTopic(name)
    topics.value.push(t)
    await selectTopic(t.id)
    await refreshStats()
    return t
  }

  async function renameTopic(id, name) {
    const updated = await updateTopic(id, { name })
    const idx = topics.value.findIndex((t) => t.id === id)
    if (idx >= 0) topics.value[idx] = { ...topics.value[idx], ...updated }
    return updated
  }

  async function removeTopic(id) {
    await deleteTopic(id)
    topics.value = topics.value.filter((t) => t.id !== id)
    if (selectedTopicId.value === id) {
      selectedTopicId.value = topics.value[0]?.id ?? null
      words.value = []
      if (selectedTopicId.value) await selectTopic(selectedTopicId.value)
    }
    await refreshStats()
  }

  async function addWord(topicId, payload) {
    const w = await saveWord(topicId, { ...payload, source_type: 'manual' })
    words.value.unshift(w)
    const t = topics.value.find((x) => x.id === topicId)
    if (t) t.word_count = (t.word_count || 0) + 1
    await refreshStats()
    return w
  }

  async function patchWord(topicId, wordId, payload) {
    const updated = await updateWord(topicId, wordId, payload)
    const idx = words.value.findIndex((w) => w.id === wordId)
    if (idx >= 0) words.value[idx] = updated
    await refreshStats()
    return updated
  }

  async function removeWord(topicId, wordId) {
    await deleteWordApi(topicId, wordId)
    words.value = words.value.filter((w) => w.id !== wordId)
    const t = topics.value.find((x) => x.id === topicId)
    if (t) t.word_count = Math.max(0, (t.word_count || 1) - 1)
    await refreshStats()
  }

  async function init() {
    await Promise.all([loadTopics(), refreshStats(), loadStudyModes()])
    if (topics.value.length && !selectedTopicId.value) {
      const defaultId = resolveDefaultTopicId(topics.value)
      if (defaultId) await selectTopic(defaultId)
    }
  }

  return {
    topics,
    topicsLoading,
    topicsError,
    words,
    wordsLoading,
    selectedTopicId,
    selectedTopic,
    stats,
    studyModes,
    canStudy,
    loadTopics,
    selectTopic,
    addTopic,
    renameTopic,
    removeTopic,
    addWord,
    patchWord,
    removeWord,
    refreshStats,
    init,
  }
}

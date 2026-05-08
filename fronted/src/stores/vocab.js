/**
 * src/stores/vocab.js
 * ────────────────────
 * Pinia store for vocabulary flashcard state.
 * DIP: Vocabulary.vue depends on this store.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client.js'

export const useVocabStore = defineStore('vocab', () => {
  // ── State ─────────────────────────────────────────────────────────────────
  const words   = ref(MOCK_WORDS)
  const loading = ref(false)

  // ── Getters ───────────────────────────────────────────────────────────────
  const totalWords = computed(() => words.value.length)

  // ── Actions ───────────────────────────────────────────────────────────────
  async function fetchWords() {
    loading.value = true
    try {
      const { data } = await apiClient.get('/vocabulary')
      words.value = data
    } catch {
      words.value = MOCK_WORDS
    } finally {
      loading.value = false
    }
  }

  async function rateWord(wordId, rating) {
    try {
      await apiClient.post(`/vocabulary/${wordId}/rate`, { rating })
    } catch {
      // silently ignore — UI still advances
    }
  }

  return { words, loading, totalWords, fetchWords, rateWord }
})

// Mock vocabulary data
const MOCK_WORDS = [
  {
    id: 1,
    word: 'Ubiquitous',
    ipa: '/juːˈbɪk.wɪ.təs/',
    type: 'adjective',
    meaning: 'Có mặt khắp nơi; phổ biến rộng rãi',
    example: 'Smartphones have become ubiquitous in modern society.',
    exampleVi: 'Điện thoại thông minh đã trở nên phổ biến trong xã hội hiện đại.',
    relatedWords: ['omnipresent', 'pervasive', 'widespread'],
    topic: 'Technology',
  },
  {
    id: 2,
    word: 'Permeate',
    ipa: '/ˈpɜː.mi.eɪt/',
    type: 'verb',
    meaning: 'Thấm qua, lan tràn khắp nơi',
    example: 'The smell of coffee permeated the entire office.',
    exampleVi: 'Mùi cà phê lan tràn khắp văn phòng.',
    relatedWords: ['penetrate', 'saturate', 'infiltrate'],
    topic: 'General',
  },
  {
    id: 3,
    word: 'Exacerbate',
    ipa: '/ɪɡˈzæs.ər.beɪt/',
    type: 'verb',
    meaning: 'Làm trầm trọng thêm, làm tệ hơn',
    example: 'The drought was exacerbated by poor water management.',
    exampleVi: 'Hạn hán bị làm trầm trọng hơn bởi quản lý nước kém.',
    relatedWords: ['aggravate', 'worsen', 'intensify'],
    topic: 'Environment',
  },
  {
    id: 4,
    word: 'Mitigate',
    ipa: '/ˈmɪt.ɪ.ɡeɪt/',
    type: 'verb',
    meaning: 'Giảm nhẹ, làm dịu đi',
    example: 'Governments must act to mitigate the effects of climate change.',
    exampleVi: 'Các chính phủ phải hành động để giảm thiểu tác động của biến đổi khí hậu.',
    relatedWords: ['alleviate', 'reduce', 'diminish'],
    topic: 'Environment',
  },
  {
    id: 5,
    word: 'Proliferate',
    ipa: '/prəˈlɪf.ər.eɪt/',
    type: 'verb',
    meaning: 'Tăng nhanh về số lượng, sinh sôi nảy nở',
    example: 'Social media platforms have proliferated over the past decade.',
    exampleVi: 'Các nền tảng mạng xã hội đã phát triển nhanh chóng trong thập kỷ qua.',
    relatedWords: ['multiply', 'expand', 'burgeon'],
    topic: 'Technology',
  },
]

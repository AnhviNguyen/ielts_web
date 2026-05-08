/**
 * src/composables/useFlashcard.js
 * ─────────────────────────────────
 * SRP: Chỉ xử lý trạng thái flashcard.
 * FSRS-inspired rating logic (simplified).
 */
import { ref, computed } from 'vue'

export function useFlashcard(words = []) {
  const currentIndex = ref(0)
  const isFlipped = ref(false)
  const sessionWords = ref([...words])

  /** Từ hiện tại */
  const currentWord = computed(() => sessionWords.value[currentIndex.value] ?? null)

  /** Tổng số từ */
  const total = computed(() => sessionWords.value.length)

  /** Lật card */
  function flip() {
    isFlipped.value = !isFlipped.value
  }

  /** Sang từ tiếp theo */
  function next() {
    isFlipped.value = false
    if (currentIndex.value < total.value - 1) {
      setTimeout(() => { currentIndex.value++ }, 150)
    }
  }

  /** Quay lại từ trước */
  function prev() {
    isFlipped.value = false
    if (currentIndex.value > 0) {
      setTimeout(() => { currentIndex.value-- }, 150)
    }
  }

  /**
   * FSRS rating — trả về interval (ngày) theo độ khó
   * @param {'again'|'hard'|'good'|'easy'} rating
   */
  function rate(rating) {
    const intervals = { again: 1, hard: 3, good: 7, easy: 14 }
    const nextInterval = intervals[rating] ?? 1
    // In real app: update word SRS data, call API
    next()
    return nextInterval
  }

  /** Reset về đầu */
  function reset() {
    currentIndex.value = 0
    isFlipped.value = false
  }

  return {
    currentIndex,
    isFlipped,
    currentWord,
    total,
    flip,
    next,
    prev,
    rate,
    reset,
  }
}

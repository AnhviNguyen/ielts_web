/**
 * src/composables/useWordCount.js
 * ────────────────────────────────
 * SRP: Chỉ đếm số từ.
 */
import { ref, computed } from 'vue'

export function useWordCount() {
  const text = ref('')

  const wordCount = computed(() => {
    const trimmed = text.value.trim()
    if (!trimmed) return 0
    return trimmed.split(/\s+/).length
  })

  function updateText(newText) {
    text.value = newText
  }

  return { text, wordCount, updateText }
}

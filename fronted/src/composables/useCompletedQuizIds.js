import { onMounted, ref } from 'vue'
import { historyService } from '@/services/historyService.js'
import { toIdSet } from '@/utils/testCompletion.js'

export function useCompletedQuizIds(subject) {
  const completedIds = ref(new Set())
  const loading = ref(false)
  const error = ref('')

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const data = await historyService.listCompletedQuizIds(subject)
      completedIds.value = toIdSet(data.quiz_ids)
    } catch (e) {
      error.value = e?.response?.data?.detail || 'Không tải được lịch sử làm bài.'
      completedIds.value = new Set()
    } finally {
      loading.value = false
    }
  }

  onMounted(load)

  return { completedIds, loading, error, reload: load }
}

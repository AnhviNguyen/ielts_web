/**
 * historyService.js — paginated practice history (GET /history).
 * History.vue uses this; dashboard may use ielts store with a larger page_size.
 */
import apiClient from '@/api/client.js'

export class HistoryService {
  /**
   * @param {{ page?: number, page_size?: number, subject?: string }} params
   * @returns {Promise<{ items, total, page, page_size, total_pages }>}
   */
  async list(params = {}) {
    const { data } = await apiClient.get('/history', { params })
    return data
  }
}

export const historyService = new HistoryService()

export function mapHistoryItem(item) {
  const skill = (item.skill || item.subject || 'reading').toLowerCase()
  return {
    id: item.id,
    skill,
    title: item.title || item.subject || 'Bài luyện IELTS',
    date: item.completed_at || item.date || '',
    duration: item.duration_seconds
      ? `${Math.max(1, Math.round(item.duration_seconds / 60))}m`
      : (item.duration || '0m'),
    score: item.band_score ?? item.score ?? item.percentage ?? 0,
    mode: item.mode || 'practice',
    quiz_id: item.quiz_id ?? null,
    session_id: item.session_id ?? item.practice_session_id ?? null,
  }
}

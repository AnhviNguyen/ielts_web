/**
 * src/stores/ielts.js
 * ────────────────────
 * Pinia store for IELTS progress, history, and band scores.
 * DIP: Views depend on this store, not on raw API calls.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ieltsService } from '@/services/ieltsService.js'

export const useIeltsStore = defineStore('ielts', () => {
  // ── State ─────────────────────────────────────────────────────────────────
  const history  = ref([])
  const progress = ref([])
  const loading  = ref(false)
  const error    = ref(null)

  const bandScores = ref({ overall: 0, reading: 0, listening: 0, writing: 0, speaking: 0 })
  const targetScores = ref({ overall: 7.0, reading: 7.5, listening: 7.0, writing: 6.5, speaking: 7.0 })
  const activityMap = ref({})
  const weeklyStats = ref([])
  const streak = ref(0)
  const daysToExam = ref(null)
  const studyPlan = ref({ days: [], message: '' })

  // ── Getters ───────────────────────────────────────────────────────────────
  const historyBySkill = computed(() => (skill) =>
    skill === 'all'
      ? history.value
      : history.value.filter(h => h.skill === skill)
  )

  // ── Actions ───────────────────────────────────────────────────────────────
  async function fetchHistory(skill = null) {
    loading.value = true
    error.value   = null
    try {
      const params = skill ? { skill } : {}
      const data = await ieltsService.getHistory(params)
      const rawItems = data.items ?? data
      history.value = rawItems.map(mapHistoryItem)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load history'
      history.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchProgress() {
    loading.value = true
    try {
      progress.value = await ieltsService.getProgress()
    } catch {
      progress.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      const data = await ieltsService.getUserStats()
      if (data.band_scores) {
        const reading = Number(data.band_scores.Reading || 0)
        const listening = Number(data.band_scores.Listening || 0)
        const writing = Number(data.band_scores.Writing || 0)
        const speaking = Number(data.band_scores.Speaking || 0)
        const overall = [reading, listening, writing, speaking].filter(Boolean).length
          ? (reading + listening + writing + speaking) / 4
          : 0
        bandScores.value = { overall, reading, listening, writing, speaking }
      }
      streak.value = Number(data.streak || 0)
      daysToExam.value = data.days_to_exam ?? null
    } catch {
      // no-op; keep defaults
    }
  }

  async function fetchPracticeAnalytics() {
    loading.value = true
    try {
      const payload = await ieltsService.getPracticeHistory({ page: 1, page_size: 200 })
      const items = payload?.items || []

      // Build activity map by completed date (YYYY-MM-DD)
      const map = {}
      for (const row of items) {
        const raw = row.completed_at || row.date
        if (!raw) continue
        const key = String(raw).slice(0, 10)
        map[key] = (map[key] || 0) + 1
      }
      activityMap.value = map

      // Build 7-day stats table from real history
      const labels = []
      const now = new Date()
      for (let i = 6; i >= 0; i--) {
        const d = new Date(now)
        d.setDate(now.getDate() - i)
        const key = d.toISOString().slice(0, 10)
        labels.push({ key, date: d.toLocaleDateString('vi-VN', { weekday: 'short' }) })
      }
      weeklyStats.value = labels.map(({ key, date }) => {
        const dayRows = items.filter((r) => String(r.completed_at || '').startsWith(key))
        const bySkill = (skill) => dayRows.filter((r) => String(r.subject || '').toLowerCase() === skill).length
        const totalSec = dayRows.reduce((sum, r) => sum + Number(r.duration_seconds || 0), 0)
        const minutes = Math.round(totalSec / 60)
        return {
          date,
          reading: bySkill('reading') || null,
          listening: bySkill('listening') || null,
          writing: bySkill('writing') || null,
          speaking: bySkill('speaking') || null,
          time: `${minutes}m`,
        }
      })
    } finally {
      loading.value = false
    }
  }

  async function fetchStudyPlan() {
    try {
      studyPlan.value = await ieltsService.getStudyPlan()
    } catch {
      studyPlan.value = { days: [], message: 'Could not load study plan' }
    }
  }

  async function generateStudyPlan() {
    try {
      studyPlan.value = await ieltsService.generateStudyPlan()
      return true
    } catch {
      return false
    }
  }

  return {
    history, progress, loading, error,
    bandScores, targetScores, activityMap, weeklyStats, streak, daysToExam, studyPlan,
    historyBySkill,
    fetchHistory, fetchProgress, fetchStats, fetchPracticeAnalytics, fetchStudyPlan, generateStudyPlan,
  }
})


function mapHistoryItem(item) {
  const skill = (item.skill || item.subject || 'reading').toLowerCase()
  return {
    id: item.id,
    skill,
    title: item.title || item.subject || 'Bài luyện IELTS',
    date: item.date || item.completed_at || '',
    duration: item.duration || (item.duration_seconds ? `${Math.round(item.duration_seconds / 60)}m` : '0m'),
    score: item.score ?? item.band_score ?? 0,
    mode: item.mode || 'practice',
  }
}

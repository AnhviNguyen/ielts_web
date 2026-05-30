/**
 * src/stores/ielts.js
 * ────────────────────
 * Pinia store for IELTS progress, history, band scores, skill radar, and study plan.
 * DIP: Views depend on this store, not on raw API calls.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ieltsService } from '@/services/ieltsService.js'
import { mapHistoryItem } from '@/services/historyService.js'

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

  // Legacy simple plan (kept for backward compat)
  const studyPlan = ref({ days: [], message: '' })

  // Skill radar: first-attempt band per skill
  const skillRadar = ref({ reading: 0, listening: 0, writing: 0, speaking: 0, attempts: {} })

  // Structured study plan tasks grouped by day
  const studyPlanData = ref({ days: [], total_tasks: 0, completed_tasks: 0 })

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
      const params = { page: 1, page_size: 100 }
      if (skill && skill !== 'all') {
        params.subject = skill.charAt(0).toUpperCase() + skill.slice(1)
      }
      const data = await ieltsService.getHistory(params)
      const rawItems = data.items ?? []
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
      const payload = await ieltsService.getHistory({ page: 1, page_size: 100 })
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
          vocabulary: bySkill('vocabulary') || null,
          time: `${minutes}m`,
        }
      })
    } finally {
      loading.value = false
    }
  }

  async function fetchStudyPlan() {
    try {
      const data = await ieltsService.getStudyPlan()
      studyPlanData.value = data
      // Backward-compat simple plan shape
      studyPlan.value = { days: data.days || [], message: '' }
    } catch {
      studyPlan.value = { days: [], message: 'Could not load study plan' }
    }
  }

  async function generateStudyPlan() {
    try {
      const data = await ieltsService.generateStudyPlan()
      studyPlanData.value = data
      studyPlan.value = { days: data.days || [], message: '' }
      return true
    } catch {
      return false
    }
  }

  async function extendStudyPlan() {
    try {
      const data = await ieltsService.extendStudyPlan()
      studyPlanData.value = data
      studyPlan.value = { days: data.days || [], message: '' }
      return true
    } catch {
      return false
    }
  }

  async function completeStudyTask(taskId) {
    try {
      const updated = await ieltsService.completeStudyTask(taskId)
      // Update in-place inside studyPlanData
      for (const day of studyPlanData.value.days || []) {
        const idx = day.tasks.findIndex(t => t.id === taskId)
        if (idx !== -1) {
          day.tasks[idx] = updated
          break
        }
      }
      // Recount completed
      const all = (studyPlanData.value.days || []).flatMap(d => d.tasks)
      studyPlanData.value.completed_tasks = all.filter(t => t.is_completed).length
      return updated
    } catch {
      return null
    }
  }

  async function fetchSkillRadar() {
    try {
      skillRadar.value = await ieltsService.getSkillRadar()
    } catch {
      // Keep zeros if not available
    }
  }

  return {
    history, progress, loading, error,
    bandScores, targetScores, activityMap, weeklyStats, streak, daysToExam,
    studyPlan, studyPlanData, skillRadar,
    historyBySkill,
    fetchHistory, fetchProgress, fetchStats, fetchPracticeAnalytics,
    fetchStudyPlan, generateStudyPlan, extendStudyPlan, completeStudyTask,
    fetchSkillRadar,
  }
})



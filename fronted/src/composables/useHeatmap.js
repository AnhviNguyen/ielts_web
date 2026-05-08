/**
 * src/composables/useHeatmap.js
 * ──────────────────────────────
 * SRP: Generate calendar heatmap data for current month.
 * Returns an array of day objects for rendering.
 */
import { computed } from 'vue'

/**
 * @param {Object} activityMap - { 'YYYY-MM-DD': count } from API
 */
export function useHeatmap(activityMap = {}) {
  const today = new Date()

  const calendarData = computed(() => {
    const year  = today.getFullYear()
    const month = today.getMonth()
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    const todayDate = today.getDate()

    // Day of week for 1st of month (0=Sun → adjust to Mon-start)
    let firstDow = new Date(year, month, 1).getDay()
    firstDow = firstDow === 0 ? 6 : firstDow - 1 // Mon=0

    const days = []

    // Empty cells before day 1
    for (let i = 0; i < firstDow; i++) {
      days.push({ day: null, empty: true, level: 0 })
    }

    // Day cells
    for (let d = 1; d <= daysInMonth; d++) {
      const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      const count = activityMap[key] ?? 0
      let level = 0
      if (count >= 3) level = 3
      else if (count === 2) level = 2
      else if (count === 1) level = 1

      days.push({
        day: d,
        empty: false,
        isToday: d === todayDate,
        level,
        count,
        key,
      })
    }

    return days
  })

  const monthLabel = computed(() => {
    return today.toLocaleDateString('vi-VN', { month: 'long', year: 'numeric' })
  })

  return { calendarData, monthLabel }
}

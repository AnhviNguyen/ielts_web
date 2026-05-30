import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'ieltstrainer_known_badges'

function loadKnown() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return new Set(JSON.parse(raw || '[]'))
  } catch {
    return new Set()
  }
}

function persistKnown(set) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...set]))
  } catch {
    /* ignore quota */
  }
}

export const useBadgeCelebrationStore = defineStore('badgeCelebration', () => {
  const queue = ref([])
  const active = ref(null)
  const knownIds = ref(loadKnown())

  function syncKnownFromBadges(items) {
    if (!Array.isArray(items)) return
    let changed = false
    for (const b of items) {
      if (b?.unlocked && b.id && !knownIds.value.has(b.id)) {
        knownIds.value.add(b.id)
        changed = true
      }
    }
    if (changed) persistKnown(knownIds.value)
  }

  function enqueue(newBadges) {
    if (!Array.isArray(newBadges) || !newBadges.length) return
    let changed = false
    for (const b of newBadges) {
      if (!b?.id || knownIds.value.has(b.id)) continue
      knownIds.value.add(b.id)
      queue.value.push(b)
      changed = true
    }
    if (changed) persistKnown(knownIds.value)
    showNext()
  }

  function showNext() {
    if (active.value) return
    if (!queue.value.length) return
    active.value = queue.value.shift()
  }

  function dismiss() {
    active.value = null
    showNext()
  }

  return {
    queue,
    active,
    enqueue,
    dismiss,
    syncKnownFromBadges,
  }
})

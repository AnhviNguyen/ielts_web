import { ref, computed, onMounted } from 'vue'

/**
 * Kéo thả để chia chiều rộng 2 cột (paneStart % · paneEnd flex).
 */
export function useSplitPane({
  storageKey = null,
  defaultPct = 33.33,
  minPct = 18,
  maxPct = 55,
} = {}) {
  const splitPct = ref(defaultPct)
  const containerRef = ref(null)
  const isResizing = ref(false)

  function clamp(n) {
    return Math.min(maxPct, Math.max(minPct, n))
  }

  onMounted(() => {
    if (!storageKey) return
    const saved = parseFloat(localStorage.getItem(storageKey))
    if (!Number.isNaN(saved)) splitPct.value = clamp(saved)
  })

  function startResize(e) {
    const el = containerRef.value
    if (!el) return
    isResizing.value = true

    const onMove = (ev) => {
      const rect = el.getBoundingClientRect()
      splitPct.value = clamp(((ev.clientX - rect.left) / rect.width) * 100)
    }

    const onUp = () => {
      isResizing.value = false
      if (storageKey) localStorage.setItem(storageKey, String(splitPct.value))
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    e.preventDefault()
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  const startPaneStyle = computed(() => ({ width: `${splitPct.value}%`, flex: 'none' }))
  const endPaneStyle = computed(() => ({ flex: '1', minWidth: 0 }))

  return {
    splitPct,
    containerRef,
    isResizing,
    startResize,
    startPaneStyle,
    endPaneStyle,
  }
}

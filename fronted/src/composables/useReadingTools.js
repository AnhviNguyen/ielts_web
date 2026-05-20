/**
 * useReadingTools – manages which reading tool (highlight / note / vocab) is active.
 *
 * SRP: Only responsible for tool state + keyboard shortcut registration.
 * Tools: 'highlight' | 'note' | 'vocab' | null
 */
import { ref, onMounted, onUnmounted } from 'vue'

const CURSOR_MAP = {
  highlight: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'24\' height=\'24\' viewBox=\'0 0 24 24\'%3E%3Cpath d=\'m9 11-6 6v3h9l3-3\' fill=\'%23854d0e\' stroke=\'%23854d0e\' stroke-width=\'1\'/%3E%3Cpath d=\'m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4\' fill=\'none\' stroke=\'%23854d0e\' stroke-width=\'2\'/%3E%3C/svg%3E") 0 24, text',
  note:      'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'24\' height=\'24\' viewBox=\'0 0 24 24\'%3E%3Cpath d=\'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7\' fill=\'none\' stroke=\'%231d4ed8\' stroke-width=\'2\'/%3E%3Cpath d=\'M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z\' fill=\'none\' stroke=\'%231d4ed8\' stroke-width=\'2\'/%3E%3C/svg%3E") 0 24, default',
  vocab:     'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'24\' height=\'24\' viewBox=\'0 0 24 24\'%3E%3Ccircle cx=\'11\' cy=\'11\' r=\'8\' fill=\'none\' stroke=\'%2315803d\' stroke-width=\'2\'/%3E%3Cline x1=\'21\' y1=\'21\' x2=\'16.65\' y2=\'16.65\' stroke=\'%2315803d\' stroke-width=\'2\'/%3E%3C/svg%3E") 12 12, crosshair',
}

const KEY_MAP = {
  t: 'highlight',
  h: 'highlight',
  n: 'note',
  s: 'vocab',
}

export function useReadingTools() {
  const activeTool = ref(null)

  function setTool(tool) {
    activeTool.value = activeTool.value === tool ? null : tool
    document.body.style.cursor = tool && activeTool.value ? CURSOR_MAP[tool] : ''
  }

  function handleKeyDown(e) {
    // Ignore if typing in input/textarea
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return
    if (e.ctrlKey || e.metaKey || e.altKey) return
    const mapped = KEY_MAP[e.key.toLowerCase()]
    if (mapped) {
      e.preventDefault()
      setTool(mapped)
    }
    if (e.key === 'Escape') {
      activeTool.value = null
      document.body.style.cursor = ''
    }
  }

  onMounted(() => window.addEventListener('keydown', handleKeyDown))
  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
    document.body.style.cursor = ''
  })

  return { activeTool, setTool, CURSOR_MAP }
}

/**
 * useTextHighlighter – handles text selection inside a DOM container and
 * persists highlights as {id, text, color, rects} objects.
 *
 * SRP: Only responsible for selection detection and highlight data management.
 */
import { ref } from 'vue'

const COLOR_BG = {
  yellow: '#fef08a',
  green:  '#bbf7d0',
  rose:   '#fecdd3',
  blue:   '#bfdbfe',
}

export function useTextHighlighter(containerRef) {
  const highlights = ref([])   // [{id, text, color, range}]

  /** Call on mouseup when highlight tool is active. */
  function applyHighlight(color = 'yellow') {
    const sel = window.getSelection()
    if (!sel || sel.isCollapsed || !containerRef.value) return

    const text = sel.toString().trim()
    if (!text) return

    // Make sure selection is inside our container
    const range = sel.getRangeAt(0)
    if (!containerRef.value.contains(range.commonAncestorContainer)) {
      sel.removeAllRanges()
      return
    }

    const id = `hl_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    highlights.value.push({ id, text, color })
    _renderHighlight(range, id, color)
    sel.removeAllRanges()
  }

  /** Rehydrate existing highlights into DOM (after content re-render) */
  function rehydrateHighlights() {
    if (!containerRef.value) return
    // Re-apply all saved highlights by searching text in DOM
    highlights.value.forEach((hl) => _applyHighlightByText(containerRef.value, hl))
  }

  /** Remove a specific highlight by id */
  function removeHighlight(id) {
    highlights.value = highlights.value.filter((h) => h.id !== id)
    if (!containerRef.value) return
    containerRef.value.querySelectorAll(`[data-hl="${id}"]`).forEach((el) => {
      const parent = el.parentNode
      while (el.firstChild) parent.insertBefore(el.firstChild, el)
      parent.removeChild(el)
      parent.normalize()
    })
  }

  /** Clear all highlights */
  function clearHighlights() {
    const ids = highlights.value.map((h) => h.id)
    ids.forEach(removeHighlight)
    highlights.value = []
  }

  // ── Private helpers ─────────────────────────────────────────────────────────

  function _renderHighlight(range, id, color) {
    try {
      const mark = document.createElement('mark')
      mark.dataset.hl = id
      mark.style.cssText = `background:${COLOR_BG[color] || COLOR_BG.yellow};border-radius:2px;padding:0 1px;cursor:pointer;`
      mark.addEventListener('click', () => removeHighlight(id))
      range.surroundContents(mark)
    } catch {
      // surroundContents fails if selection crosses element boundaries – use extractContents
      try {
        const frag = range.extractContents()
        const mark = document.createElement('mark')
        mark.dataset.hl = id
        mark.style.cssText = `background:${COLOR_BG[color] || COLOR_BG.yellow};border-radius:2px;padding:0 1px;cursor:pointer;`
        mark.addEventListener('click', () => removeHighlight(id))
        mark.appendChild(frag)
        range.insertNode(mark)
      } catch (_) { /* silent */ }
    }
  }

  function _applyHighlightByText(container, hl) {
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT)
    let node
    while ((node = walker.nextNode())) {
      const idx = node.textContent.indexOf(hl.text)
      if (idx === -1) continue
      const range = document.createRange()
      range.setStart(node, idx)
      range.setEnd(node, idx + hl.text.length)
      _renderHighlight(range, hl.id, hl.color)
      break
    }
  }

  return { highlights, applyHighlight, rehydrateHighlights, removeHighlight, clearHighlights, COLOR_BG }
}

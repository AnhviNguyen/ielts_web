import { computed, nextTick, ref } from 'vue'

// ── helpers ────────────────────────────────────────────────────────────────

/**
 * Normalise locate_info into an array of paragraph_range objects.
 * Handles both:
 *   { paragraph_ranges: [...] }
 *   { "0": { paragraph_ranges: [...] }, "1": { paragraph_ranges: [...] } }
 */
function normaliseRanges(locateInfo) {
  if (!locateInfo) return []
  if (Array.isArray(locateInfo.paragraph_ranges)) return locateInfo.paragraph_ranges
  // keyed form (MULTIPLE_CHOICE_MANY etc.)
  return Object.values(locateInfo).flatMap(v =>
    Array.isArray(v?.paragraph_ranges) ? v.paragraph_ranges : []
  )
}

/**
 * Given a single paragraph_range and the flat paragraphs array,
 * return the child (sentence) IDs that fall within the range.
 *
 * Data contract:
 *  - range.start / range.end have { paragraph: 1-based, sentence?: 1-based }
 *  - paragraphs[i].paragraph === i+1  (built by buildParagraphsFromVocabs)
 *  - paragraphs[i].children[j] is sentence j+1 of that paragraph
 */
function idsFromRange(paragraphs, range) {
  const { start, end } = range || {}
  if (!start || !end) return []

  const pStart = start.paragraph
  const pEnd   = end.paragraph
  const sStart = start.sentence ?? 1
  const sEnd   = end.sentence   ?? Infinity

  const ids = []
  for (const p of paragraphs) {
    const pIdx = p.paragraph
    if (pIdx < pStart || pIdx > pEnd) continue

    const children = p.children || []
    children.forEach((c, i) => {
      const si = i + 1 // 1-based sentence index within this paragraph
      if (pIdx === pStart && pIdx === pEnd) {
        if (si >= sStart && si <= sEnd) ids.push(c.id)
      } else if (pIdx === pStart) {
        if (si >= sStart) ids.push(c.id)
      } else if (pIdx === pEnd) {
        if (si <= sEnd) ids.push(c.id)
      } else {
        ids.push(c.id) // middle paragraphs: all sentences
      }
    })
  }
  return ids
}

// ── composable ─────────────────────────────────────────────────────────────

/**
 * @param {import('vue').Ref<Array>} paragraphsRef  – reactive ref to paragraph array
 *        (output of buildParagraphsFromVocabs, 1-based paragraph indices)
 * @param {import('vue').Ref<number>} currentTimeRef – reactive audio currentTime
 *
 * @returns {{
 *   segments: ComputedRef,
 *   activeSegId: ComputedRef<string|null>,
 *   highlightedIds: ComputedRef<Set>,
 *   activateLocateInfo(locateInfo: object): void,
 *   clearForced(): void,
 *   scrollToSegId: Ref<string|null>,   // sentinel: changes → caller should scroll
 * }}
 */
export function useTranscript(paragraphsRef, currentTimeRef) {
  // ── flat sentence list ───────────────────────────────────────────
  const segments = computed(() => {
    const out = []
    for (const p of (paragraphsRef.value || [])) {
      for (const c of (p.children || [])) {
        if (!Number.isFinite(c.from) || !Number.isFinite(c.to)) continue
        out.push({ id: c.id, from: c.from, to: c.to, speaker: c.speaker, text: c.text })
      }
    }
    return out
  })

  // ── time-based active segment ────────────────────────────────────
  const activeSegId = computed(() => {
    const t = currentTimeRef.value || 0
    return segments.value.find(s => t >= s.from && t <= s.to)?.id ?? null
  })

  // ── forced highlight (from question play button) ─────────────────
  const _forcedIds = ref(/** @type {Set<string>} */ (new Set()))
  let _clearTimer  = null

  /**
   * Parse locate_info → find sentence IDs → force-highlight them for 5 s.
   * After 5 s they are cleared automatically.
   */
  function activateLocateInfo(locateInfo) {
    const paragraphs = paragraphsRef.value || []
    const ranges = normaliseRanges(locateInfo)
    const ids = ranges.flatMap(r => idsFromRange(paragraphs, r))
    _forcedIds.value = new Set(ids)
    clearTimeout(_clearTimer)
    if (ids.length) {
      _clearTimer = setTimeout(() => { _forcedIds.value = new Set() }, 5000)
    }
  }

  function clearForced() {
    clearTimeout(_clearTimer)
    _forcedIds.value = new Set()
  }

  // ── merged: forced takes priority, else time-based ───────────────
  const highlightedIds = computed(() => {
    if (_forcedIds.value.size > 0) return _forcedIds.value
    return activeSegId.value ? new Set([activeSegId.value]) : new Set()
  })

  /**
   * When the caller should scroll the transcript, this ref changes to the
   * target segment ID.  Consumers can watch it.
   */
  const scrollToSegId = computed(() => {
    if (_forcedIds.value.size > 0) return [..._forcedIds.value][0]
    return activeSegId.value
  })

  return {
    segments,
    activeSegId,
    highlightedIds,
    scrollToSegId,
    activateLocateInfo,
    clearForced,
  }
}

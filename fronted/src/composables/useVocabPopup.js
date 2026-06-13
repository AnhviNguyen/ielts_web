/**
 * useVocabPopup – word lookup + popup for Reading/Listening/Shadowing passages.
 */
import { ref } from 'vue'
import { searchWords } from '@/services/vocabularyService.js'
import { fetchLookupWord } from '@/services/vocabLookupService.js'
import { getCachedLookup, setCachedLookup } from '@/utils/vocabLookupCache.js'

export function useVocabPopup() {
  const popupVisible = ref(false)
  const popupWord    = ref(null)
  const popupPos     = ref({ x: 0, y: 0 })
  const popupLoading = ref(false)
  const hoveredWord  = ref(null)

  function bindContainer(container) {
    if (!container) return
    _wrapWords(container)
    container.querySelectorAll('.vocab-word').forEach((span) => {
      span.addEventListener('mouseenter', () => {
        hoveredWord.value = span.textContent.trim()
        span.classList.add('vocab-underline')
      })
      span.addEventListener('mouseleave', () => {
        span.classList.remove('vocab-underline')
      })
      span.addEventListener('click', (e) => {
        e.stopPropagation()
        openPopup(span.textContent.trim(), e.clientX, e.clientY)
      })
    })
  }

  function unbindContainer(container) {
    if (!container) return
    container.querySelectorAll('.vocab-word').forEach((span) => {
      span.classList.remove('vocab-underline')
    })
  }

  async function openPopup(word, x, y) {
    const clean = word.replace(/[^a-zA-Z'-]/g, '').toLowerCase()
    if (!clean) return
    popupPos.value = { x, y }
    popupVisible.value = true
    popupLoading.value = true
    popupWord.value = { word: clean, phonetic: '', meaning_en: '', meaning_vi: '', example: '', example_vi: '', audio: '', allMeanings: [] }

    const cached = getCachedLookup(clean)
    if (cached) {
      popupWord.value = { ...cached }
      popupLoading.value = false
      return
    }

    const saved = await _tryUserSavedWord(clean)
    if (saved) {
      popupWord.value = saved
      setCachedLookup(clean, saved)
      popupLoading.value = false
      return
    }

    try {
      const result = await fetchLookupWord(clean)
      popupWord.value = _normalizeResult(result, clean)
      setCachedLookup(clean, popupWord.value)
    } catch {
      popupWord.value = _emptyLookup(clean)
    } finally {
      popupLoading.value = false
    }
  }

  function closePopup() {
    popupVisible.value = false
    popupWord.value = null
  }

  function speak(word) {
    if (!window.speechSynthesis) return
    const utt = new SpeechSynthesisUtterance(word)
    utt.lang = 'en-US'
    utt.rate = 0.9
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utt)
  }

  return {
    popupVisible, popupWord, popupPos, popupLoading, hoveredWord,
    bindContainer, unbindContainer, openPopup, closePopup, speak,
  }
}

export async function lookupWord(word) {
  const clean = word.replace(/[^a-zA-Z'-]/g, '').toLowerCase()
  if (!clean) return _emptyLookup(word)

  const cached = getCachedLookup(clean)
  if (cached) return { ...cached }

  const saved = await _tryUserSavedWord(clean)
  if (saved) return saved

  try {
    const result = _normalizeResult(await fetchLookupWord(clean), clean)
    setCachedLookup(clean, result)
    return result
  } catch {
    return _emptyLookup(clean)
  }
}

function _normalizeResult(raw, word) {
  return {
    word: raw.word || word,
    phonetic: raw.phonetic || '',
    word_type: raw.word_type || '',
    meaning_en: raw.meaning_en || '',
    meaning_vi: raw.meaning_vi || '',
    example: raw.example || '',
    example_vi: raw.example_vi || '',
    audio: raw.audio || '',
    allMeanings: raw.allMeanings || raw.all_meanings || [],
  }
}

async function _tryUserSavedWord(word) {
  try {
    const hits = await searchWords(word)
    const hit = hits?.find((h) => h.word?.toLowerCase() === word)
    if (!hit) return null
    return {
      word: hit.word,
      phonetic: hit.phonetic || '',
      word_type: hit.word_type || '',
      meaning_en: hit.meaning_en || '',
      meaning_vi: hit.meaning_vi || '',
      example: hit.example || '',
      example_vi: hit.example_vi || '',
      audio: '',
      allMeanings: hit.meaning_en || hit.meaning_vi
        ? [{ type: hit.word_type || '', defs: [hit.meaning_vi || hit.meaning_en], example: hit.example || '' }]
        : [],
      _fromSaved: true,
    }
  } catch {
    return null
  }
}

function _emptyLookup(word) {
  return {
    word,
    phonetic: '',
    word_type: '',
    meaning_en: '',
    meaning_vi: '',
    example: '',
    example_vi: '',
    audio: '',
    allMeanings: [],
  }
}

function _wrapWords(container) {
  if (container.dataset.vocabWrapped) return
  container.dataset.vocabWrapped = '1'

  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => {
      const parent = n.parentElement
      if (!parent) return NodeFilter.FILTER_REJECT
      const tag = parent.tagName
      if (['SCRIPT', 'STYLE', 'MARK'].includes(tag)) return NodeFilter.FILTER_REJECT
      if (parent.classList.contains('vocab-word')) return NodeFilter.FILTER_REJECT
      return NodeFilter.FILTER_ACCEPT
    },
  })

  const nodes = []
  let node
  while ((node = walker.nextNode())) nodes.push(node)

  nodes.forEach((textNode) => {
    const frag = document.createDocumentFragment()
    const words = textNode.textContent.split(/(\s+)/)
    words.forEach((part) => {
      if (/^\s+$/.test(part)) {
        frag.appendChild(document.createTextNode(part))
      } else if (part) {
        const span = document.createElement('span')
        span.className = 'vocab-word'
        span.textContent = part
        frag.appendChild(span)
      }
    })
    textNode.parentNode.replaceChild(frag, textNode)
  })
}

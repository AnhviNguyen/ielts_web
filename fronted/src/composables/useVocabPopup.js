/**
 * useVocabPopup – manages vocabulary hover (underline) and click (popup) in
 * a reading passage when the "vocab" tool is active.
 *
 * SRP: Only responsible for word detection, API lookup, and popup positioning.
 */
import { ref } from 'vue'

export function useVocabPopup() {
  const popupVisible = ref(false)
  const popupWord    = ref(null)   // { word, phonetic, word_type, meaning_vi, example, example_vi }
  const popupPos     = ref({ x: 0, y: 0 })
  const popupLoading = ref(false)
  const hoveredWord  = ref(null)   // currently underlined word

  /** Attach hover + click events to every word span inside `container`. */
  function bindContainer(container) {
    if (!container) return
    // Wrap every text node's words in <span class="vocab-word">
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

  /** Unbind hover effects (when switching away from vocab tool) */
  function unbindContainer(container) {
    if (!container) return
    container.querySelectorAll('.vocab-word').forEach((span) => {
      span.classList.remove('vocab-underline')
    })
  }

  async function openPopup(word, x, y) {
    const clean = word.replace(/[^a-zA-Z'-]/g, '').toLowerCase()
    if (!clean) return
    popupPos.value    = { x, y }
    popupVisible.value = true
    popupLoading.value = true
    popupWord.value    = null
    try {
      const data = await lookupWord(clean)
      popupWord.value = data
    } finally {
      popupLoading.value = false
    }
  }

  function closePopup() {
    popupVisible.value = false
    popupWord.value    = null
  }

  /** Speak a word using Web Speech API */
  function speak(word) {
    if (!window.speechSynthesis) return
    const utt = new SpeechSynthesisUtterance(word)
    utt.lang = 'en-US'
    utt.rate = 0.9
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utt)
  }

  return { popupVisible, popupWord, popupPos, popupLoading, hoveredWord, bindContainer, unbindContainer, openPopup, closePopup, speak }
}

// ── Dictionary lookup (Free Dictionary API + MyMemory Vietnamese translation) ─

export async function lookupWord(word) {
  try {
    // Run English definition + Vietnamese translation in parallel
    const [dictData, viData] = await Promise.allSettled([
      _fetchEnglishDef(word),
      _fetchVietnamese(word),
    ])

    const entry = dictData.status === 'fulfilled' ? dictData.value : null
    const meaning_vi = viData.status === 'fulfilled' ? viData.value : ''

    if (!entry) {
      return { word, phonetic: '', word_type: '', meaning_vi, example: '', example_vi: '', audio: '', allMeanings: [] }
    }

    const firstMeaning = entry.meanings?.[0] ?? {}
    const firstDef     = firstMeaning.definitions?.[0] ?? {}

    return {
      word:       entry.word,
      phonetic:   entry.phonetic || entry.phonetics?.find(p => p.text)?.text || '',
      word_type:  firstMeaning.partOfSpeech || '',
      meaning_vi,
      example:    firstDef.example || '',
      example_vi: '',
      audio:      entry.phonetics?.find(p => p.audio)?.audio || '',
      allMeanings: entry.meanings?.slice(0, 3).map(m => ({
        type:    m.partOfSpeech,
        defs:    m.definitions.slice(0, 2).map(d => d.definition),
        example: m.definitions[0]?.example || '',
      })) || [],
    }
  } catch {
    return { word, phonetic: '', word_type: '', meaning_vi: '', example: '', example_vi: '', audio: '', allMeanings: [] }
  }
}

async function _fetchEnglishDef(word) {
  const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`)
  if (!res.ok) throw new Error('not found')
  const data = await res.json()
  return data[0]
}

async function _fetchVietnamese(word) {
  try {
    const res = await fetch(
      `https://api.mymemory.translated.net/get?q=${encodeURIComponent(word)}&langpair=en%7Cvi&de=a@b.com`
    )
    if (!res.ok) return ''
    const data = await res.json()
    const translated = data?.responseData?.translatedText || ''
    // MyMemory returns the same word if it can't translate or returns non-Vietnamese, filter those out
    if (!translated || translated.toLowerCase() === word.toLowerCase()) return ''
    return translated
  } catch {
    return ''
  }
}

// ── Word wrapping helper ──────────────────────────────────────────────────────

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

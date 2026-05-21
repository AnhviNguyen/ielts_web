/**
 * useVocabPopup – word lookup + popup for Reading/Listening passages.
 */
import { ref } from 'vue'

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
    popupWord.value = null
    try {
      popupWord.value = await lookupWord(clean)
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
  try {
    const [dictData, viData, exViData] = await Promise.allSettled([
      _fetchEnglishDef(word),
      _fetchVietnamese(word),
      null,
    ])

    const entry = dictData.status === 'fulfilled' ? dictData.value : null
    const meaning_vi = viData.status === 'fulfilled' ? viData.value : ''

    if (!entry) {
      return _emptyLookup(word, meaning_vi)
    }

    const firstMeaning = entry.meanings?.[0] ?? {}
    const firstDef = firstMeaning.definitions?.[0] ?? {}
    const example = firstDef.example || ''
    const meaning_en = _buildEnglishGloss(entry)

    let example_vi = ''
    if (example) {
      const tr = await _fetchVietnamese(example)
      example_vi = tr || ''
    }

    return {
      word: entry.word,
      phonetic: entry.phonetic || entry.phonetics?.find((p) => p.text)?.text || '',
      word_type: firstMeaning.partOfSpeech || '',
      meaning_en,
      meaning_vi,
      example,
      example_vi,
      audio: entry.phonetics?.find((p) => p.audio)?.audio || '',
      allMeanings: entry.meanings?.slice(0, 3).map((m) => ({
        type: m.partOfSpeech,
        defs: m.definitions.slice(0, 2).map((d) => d.definition),
        example: m.definitions[0]?.example || '',
      })) || [],
    }
  } catch {
    return _emptyLookup(word, '')
  }
}

function _emptyLookup(word, meaning_vi) {
  return {
    word, phonetic: '', word_type: '', meaning_en: '', meaning_vi,
    example: '', example_vi: '', audio: '', allMeanings: [],
  }
}

function _buildEnglishGloss(entry) {
  const parts = []
  for (const m of (entry.meanings || []).slice(0, 2)) {
    const pos = m.partOfSpeech ? `(${m.partOfSpeech}) ` : ''
    for (const d of (m.definitions || []).slice(0, 2)) {
      if (d.definition) parts.push(`${pos}${d.definition}`)
    }
  }
  return parts.join('; ')
}

async function _fetchEnglishDef(word) {
  const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`)
  if (!res.ok) throw new Error('not found')
  const data = await res.json()
  return data[0]
}

async function _fetchVietnamese(text) {
  try {
    const q = encodeURIComponent(String(text).slice(0, 200))
    const res = await fetch(
      `https://api.mymemory.translated.net/get?q=${q}&langpair=en%7Cvi&de=a@b.com`
    )
    if (!res.ok) return ''
    const data = await res.json()
    const translated = data?.responseData?.translatedText || ''
    if (!translated || translated.toLowerCase() === String(text).toLowerCase()) return ''
    return translated
  } catch {
    return ''
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

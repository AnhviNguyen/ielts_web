<template>
  <Teleport to="body">
    <Transition name="popup-fade">
      <div
        v-if="visible"
        ref="popupEl"
        class="vocab-popup fixed z-[9000] flex w-[min(420px,calc(100vw-24px))] max-h-[min(560px,calc(100vh-24px))] flex-col overflow-hidden rounded-[var(--radius-comfortable)] border border-[var(--border-button)] bg-[var(--bg-surface)] text-[13px] text-[var(--text-base)] shadow-[var(--shadow-heavy)]"
        :style="posStyle"
        @click.stop
      >
        <div class="flex shrink-0 items-start justify-between gap-2 border-b border-[var(--border-button)] px-4 pb-2.5 pt-3.5">
          <div class="min-w-0">
            <div class="text-lg font-extrabold text-[var(--text-base)]">{{ word?.word || '…' }}</div>
            <div v-if="word?.phonetic" class="mt-0.5 font-mono text-xs text-[var(--text-subdued)]">/{{ word.phonetic }}/</div>
            <span v-if="word?.word_type" class="ct-badge mt-1">{{ word.word_type }}</span>
          </div>
          <div class="flex shrink-0 items-center gap-1">
            <button
              type="button"
              class="ct-btn flex h-8 w-8 items-center justify-center !rounded-full !p-0 hover:!border-[var(--spotify-green)] hover:!bg-[var(--spotify-green)] hover:!text-[var(--bubble-user-text)]"
              title="Phát âm"
              @click="speak"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
              </svg>
            </button>
            <button
              type="button"
              class="ct-btn flex h-8 w-8 items-center justify-center !rounded-full !p-0"
              title="Đóng"
              @click="$emit('close')"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>

        <div v-if="loading && !hasAnyContent" class="flex items-center gap-2 px-4 py-4 text-xs text-[var(--text-subdued)]">
          <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M22 12a10 10 0 0 1-10 10"/></svg>
          Đang tra từ…
        </div>

        <template v-else-if="word">
          <div
            class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-contain [scrollbar-width:thin] [scrollbar-color:var(--border-button)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-[var(--border-outlined)]"
          >
            <section v-if="word.meaning_en" class="border-b border-[var(--border-button)] bg-[var(--bg-interactive)] px-3.5 py-2.5">
              <span class="mb-1.5 inline-block rounded-md bg-[var(--blue-bg)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--text-announcement)]">English</span>
              <div class="break-words leading-relaxed text-[var(--text-base)]">{{ word.meaning_en }}</div>
            </section>

            <section v-if="word.meaning_vi" class="border-b border-[var(--border-button)] px-3.5 py-2.5">
              <span class="mb-1.5 inline-block rounded-md bg-[var(--green-bg)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--spotify-green)]">Tiếng Việt</span>
              <div class="text-sm font-semibold leading-relaxed text-[var(--spotify-green)]">{{ word.meaning_vi }}</div>
            </section>

            <div
              v-for="(m, i) in detailMeanings"
              :key="i"
              class="border-b border-[var(--border-button)] px-3.5 py-2.5"
            >
              <span v-if="m.type" class="ct-badge mb-1.5">{{ m.type }}</span>
              <div v-for="(def, j) in m.defs" :key="j" class="mb-0.5 break-words leading-relaxed text-[var(--text-base)]">{{ j + 1 }}. {{ def }}</div>
            </div>

            <section v-if="word.example" class="border-b border-[var(--border-button)] px-3.5 py-2.5">
              <span class="mb-1.5 inline-block rounded-md bg-[var(--amber-bg)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--text-warning)]">Example</span>
              <div class="text-[13px] italic leading-snug text-[var(--text-subdued)]">{{ word.example }}</div>
              <div v-if="word.example_vi" class="mt-1.5 text-[12px] text-[var(--spotify-green)]">{{ word.example_vi }}</div>
            </section>

            <div
              v-if="!hasAnyMeaning && !loading"
              class="px-3.5 py-3 text-xs text-[var(--text-subdued)]"
            >
              Không tìm thấy nghĩa đầy đủ. Bạn vẫn có thể lưu từ và chỉnh sửa trên trang Từ vựng.
            </div>
          </div>

          <div class="flex shrink-0 items-stretch gap-2 border-t border-[var(--border-button)] bg-[var(--bg-surface)] px-4 py-3">
            <button type="button" class="ct-btn flex h-10 min-w-0 flex-1 items-center justify-center gap-1.5" @click="copyWord">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {{ copied ? 'Đã sao chép' : 'Sao chép' }}
            </button>
            <button type="button" class="btn btn-primary flex h-10 min-w-0 flex-1 items-center justify-center gap-1.5" @click="$emit('save', word)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
              + Lưu từ vựng
            </button>
          </div>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible:  { type: Boolean, default: false },
  word:     { type: Object,  default: null },
  loading:  { type: Boolean, default: false },
  position: { type: Object,  default: () => ({ x: 0, y: 0 }) },
})
const emit = defineEmits(['close', 'save'])

const popupEl = ref(null)
const copied  = ref(false)

const POPUP_WIDTH = 420
const POPUP_MAX_HEIGHT = 560

const posStyle = computed(() => {
  const PAD = 12
  const W = POPUP_WIDTH
  const H = POPUP_MAX_HEIGHT
  let x = props.position.x + PAD
  let y = props.position.y + PAD
  if (x + W > window.innerWidth - PAD) x = props.position.x - W - PAD
  if (y + H > window.innerHeight - PAD) y = props.position.y - H - PAD
  return {
    left: `${Math.max(PAD, x)}px`,
    top: `${Math.max(PAD, y)}px`,
    maxHeight: `min(${POPUP_MAX_HEIGHT}px, calc(100vh - ${PAD * 2}px))`,
  }
})

const detailMeanings = computed(() => {
  const list = props.word?.allMeanings || []
  return list.filter((m) => m.defs?.length)
})

const hasAnyMeaning = computed(() => {
  const w = props.word
  if (!w) return false
  return !!(w.meaning_en || w.meaning_vi || detailMeanings.value.length)
})

const hasAnyContent = computed(() => hasAnyMeaning.value || props.word?.phonetic || props.word?.example)

function speak() {
  if (!props.word?.word) return
  if (props.word.audio) {
    const a = new Audio(props.word.audio)
    a.play().catch(() => _speakBrowser(props.word.word))
    return
  }
  _speakBrowser(props.word.word)
}

function _speakBrowser(text) {
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = 'en-US'
  utt.rate = 0.9
  window.speechSynthesis?.cancel()
  window.speechSynthesis?.speak(utt)
}

function copyWord() {
  const w = props.word
  if (!w) return
  const lines = [w.word]
  if (w.phonetic) lines.push(`/${w.phonetic}/`)
  if (w.meaning_en) lines.push(`EN: ${w.meaning_en}`)
  if (w.meaning_vi) lines.push(`VI: ${w.meaning_vi}`)
  if (w.example) lines.push(`Ex: ${w.example}`)
  if (w.example_vi) lines.push(`VD: ${w.example_vi}`)
  navigator.clipboard?.writeText(lines.join('\n'))
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

function onClickOutside(e) {
  if (props.visible && popupEl.value && !popupEl.value.contains(e.target)) {
    emit('close')
  }
}

onMounted(() => window.addEventListener('mousedown', onClickOutside, true))
onUnmounted(() => window.removeEventListener('mousedown', onClickOutside, true))
</script>

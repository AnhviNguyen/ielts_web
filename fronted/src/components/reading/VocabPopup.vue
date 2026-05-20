<template>
  <Teleport to="body">
    <Transition name="popup-fade">
      <div
        v-if="visible"
        ref="popupEl"
        class="vocab-popup"
        :style="posStyle"
        @click.stop
      >
        <!-- Header: word + phonetic + TTS -->
        <div class="vocab-popup__header">
          <div>
            <div class="vocab-popup__word">{{ word?.word }}</div>
            <div v-if="word?.phonetic" class="vocab-popup__phonetic">/ {{ word.phonetic }} /</div>
          </div>
          <div class="vocab-popup__actions-top">
            <button class="vocab-popup__icon-btn" title="Phát âm" @click="speak">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
              </svg>
            </button>
            <button class="vocab-popup__icon-btn" title="Đóng" @click="$emit('close')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="vocab-popup__loading">
          <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M22 12a10 10 0 0 1-10 10"/></svg>
          Đang tra từ...
        </div>

        <template v-else-if="word">
          <!-- Word type + Vietnamese meaning -->
          <div v-for="(m, i) in (word.allMeanings?.length ? word.allMeanings : defaultMeanings)" :key="i" class="vocab-popup__meaning-block">
            <span class="vocab-popup__word-type">{{ m.type }}</span>
            <div v-if="word.meaning_vi && i === 0" class="vocab-popup__vi">{{ word.meaning_vi }}</div>
            <div v-for="(def, j) in m.defs" :key="j" class="vocab-popup__def">{{ j + 1 }}. {{ def }}</div>
            <div v-if="m.example" class="vocab-popup__example">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/></svg>
              {{ m.example }}
            </div>
          </div>

          <!-- Save + Copy -->
          <div class="vocab-popup__footer">
            <button class="vocab-popup__copy-btn" @click="copyWord" title="Sao chép">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              {{ copied ? 'Đã sao chép' : 'Sao chép' }}
            </button>
            <button class="vocab-popup__save-btn" @click="$emit('save', word)" title="Lưu từ vựng">
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible:  { type: Boolean, default: false },
  word:     { type: Object,  default: null },
  loading:  { type: Boolean, default: false },
  position: { type: Object,  default: () => ({ x: 0, y: 0 }) },
})
const emit = defineEmits(['close', 'save'])

const popupEl = ref(null)
const copied  = ref(false)

const posStyle = computed(() => {
  const PAD = 12
  const W = 300, H = 320
  let x = props.position.x + PAD
  let y = props.position.y + PAD
  if (x + W > window.innerWidth  - PAD) x = props.position.x - W - PAD
  if (y + H > window.innerHeight - PAD) y = props.position.y - H - PAD
  return { left: `${Math.max(PAD, x)}px`, top: `${Math.max(PAD, y)}px` }
})

const defaultMeanings = computed(() => {
  if (!props.word) return []
  return [{ type: props.word.word_type, defs: [], example: props.word.example }]
})

function speak() {
  if (!props.word?.word) return
  const utt = new SpeechSynthesisUtterance(props.word.word)
  utt.lang = 'en-US'
  utt.rate = 0.9
  window.speechSynthesis?.cancel()
  window.speechSynthesis?.speak(utt)
}

function copyWord() {
  navigator.clipboard?.writeText(props.word?.word || '')
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

<style scoped>
.vocab-popup {
  position: fixed;
  z-index: 9000;
  width: 300px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,.15);
  overflow: hidden;
  font-size: 13px;
}

.vocab-popup__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  padding: 14px 14px 10px;
  border-bottom: 1px solid #f1f5f9;
}

.vocab-popup__word {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
}

.vocab-popup__phonetic {
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
  font-style: italic;
}

.vocab-popup__actions-top {
  display: flex;
  gap: 4px;
  align-items: center;
  flex-shrink: 0;
}

.vocab-popup__icon-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: #f8fafc;
  color: #475569;
  transition: all .15s;
}
.vocab-popup__icon-btn:hover { background: #15803d; color: #fff; border-color: #15803d; }

.vocab-popup__loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: #94a3b8;
  font-size: 12px;
}

.vocab-popup__meaning-block {
  padding: 10px 14px;
  border-bottom: 1px solid #f8fafc;
}

.vocab-popup__word-type {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  background: #dcfce7;
  color: #15803d;
  border-radius: 6px;
  padding: 1px 8px;
  margin-bottom: 6px;
}

.vocab-popup__vi {
  font-size: 14px;
  font-weight: 700;
  color: #15803d;
  margin-bottom: 4px;
}

.vocab-popup__def {
  color: #374151;
  line-height: 1.6;
  margin-bottom: 2px;
}

.vocab-popup__example {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 6px;
  padding: 6px 8px;
  border-radius: 8px;
  background: #f0fdf4;
  color: #15803d;
  font-style: italic;
  font-size: 11px;
  line-height: 1.5;
}

.vocab-popup__footer {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
}

.vocab-popup__copy-btn,
.vocab-popup__save-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
}

.vocab-popup__copy-btn {
  flex: 1;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  justify-content: center;
}
.vocab-popup__copy-btn:hover { border-color: #94a3b8; background: #f1f5f9; }

.vocab-popup__save-btn {
  flex: 2;
  border: 1px solid #15803d;
  background: #15803d;
  color: #fff;
  justify-content: center;
}
.vocab-popup__save-btn:hover { background: #166534; }

/* Transition */
.popup-fade-enter-active, .popup-fade-leave-active { transition: opacity .15s, transform .15s; }
.popup-fade-enter-from, .popup-fade-leave-to { opacity: 0; transform: scale(.95); }
</style>

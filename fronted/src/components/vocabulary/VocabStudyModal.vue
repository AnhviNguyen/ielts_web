<template>
  <Teleport to="body">
    <Transition name="study-fade">
      <div v-if="show" class="study-overlay" @click.self="$emit('close')">
        <div class="study-box">

          <!-- ── Header ─────────────────────────────────────────── -->
          <div class="study-header">
            <div class="study-header__left">
              <div class="study-title">Luyện tập từ vựng</div>
              <div class="study-sub">{{ topicName }} · {{ doneCount }}/{{ queue.length }} từ</div>
            </div>
            <button class="study-close" @click="$emit('close')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- ── Progress bar ────────────────────────────────────── -->
          <div class="study-progress-wrap">
            <div class="study-progress-bar" :style="{ width: `${progressPct}%` }"></div>
          </div>

          <!-- ── Mode badges ────────────────────────────────────── -->
          <div class="mode-tabs">
            <button
              v-for="m in MODES" :key="m.id"
              class="mode-tab"
              :class="{ active: currentMode === m.id }"
              @click="currentMode = m.id; resetCard()"
            >
              <span v-html="m.icon"></span>
              {{ m.label }}
            </button>
          </div>

          <!-- ── Completed screen ──────────────────────────────── -->
          <div v-if="completed" class="done-screen">
            <div class="done-emoji">🎉</div>
            <div class="done-title">Hoàn thành lượt ôn!</div>
            <div class="done-sub">{{ correctCount }}/{{ doneCount }} đúng</div>
            <div class="done-actions">
              <button class="btn-secondary" @click="$emit('close')">Đóng</button>
              <button class="btn-primary" @click="restartSession">Ôn lại</button>
            </div>
          </div>

          <!-- ── Card area ─────────────────────────────────────── -->
          <template v-else-if="currentWord">

            <!-- ── FLASHCARD ─────────────────────────────────────── -->
            <div v-if="currentMode === 'flashcard'" class="card-area">
              <div class="flashcard" :class="{ flipped: cardFlipped }" @click="cardFlipped = !cardFlipped">
                <div class="flashcard-front">
                  <div class="fc-word">{{ currentWord.word }}</div>
                  <div v-if="currentWord.phonetic" class="fc-phonetic">/ {{ currentWord.phonetic }} /</div>
                  <div v-if="currentWord.word_type" class="fc-type">{{ currentWord.word_type }}</div>
                  <div class="fc-hint">Nhấn để xem nghĩa</div>
                </div>
                <div class="flashcard-back">
                  <div class="fc-meaning">{{ currentWord.meaning_vi || '—' }}</div>
                  <div v-if="currentWord.example" class="fc-example">{{ currentWord.example }}</div>
                </div>
              </div>

              <div v-if="cardFlipped" class="fc-actions">
                <button class="fc-btn fc-btn--wrong" @click="markAnswer(false)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  Chưa nhớ
                </button>
                <button class="fc-btn fc-btn--correct" @click="markAnswer(true)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
                  Đã nhớ
                </button>
              </div>
              <div v-else class="fc-tip">Nhấn vào thẻ để lật</div>
            </div>

            <!-- ── MULTIPLE CHOICE ──────────────────────────────── -->
            <div v-else-if="currentMode === 'multiple'" class="card-area">
              <div class="mc-question">
                <div class="mc-word">{{ currentWord.word }}</div>
                <div v-if="currentWord.phonetic" class="mc-phonetic">/ {{ currentWord.phonetic }} /</div>
                <div class="mc-prompt">Chọn nghĩa đúng của từ trên:</div>
              </div>
              <div class="mc-options">
                <button
                  v-for="(opt, i) in mcOptions" :key="i"
                  class="mc-option"
                  :class="{
                    correct:   answered && opt.correct,
                    wrong:     answered && !opt.correct && opt === selectedOption,
                    disabled:  answered && !opt.correct && opt !== selectedOption,
                  }"
                  :disabled="answered"
                  @click="selectMcOption(opt)"
                >
                  <span class="mc-letter">{{ 'ABCD'[i] }}</span>
                  <span>{{ opt.text }}</span>
                </button>
              </div>
              <div v-if="answered" class="answer-result" :class="lastCorrect ? 'result--correct' : 'result--wrong'">
                {{ lastCorrect ? '✓ Chính xác!' : `✗ Đáp án đúng: ${currentWord.meaning_vi}` }}
              </div>
              <button v-if="answered" class="btn-next" @click="nextWord">Tiếp theo →</button>
            </div>

            <!-- ── TYPING ────────────────────────────────────────── -->
            <div v-else-if="currentMode === 'typing'" class="card-area">
              <div class="tp-question">
                <div class="tp-label">Gõ từ tiếng Anh có nghĩa là:</div>
                <div class="tp-meaning">{{ currentWord.meaning_vi }}</div>
                <div v-if="currentWord.example" class="tp-example">{{ exampleWithBlank }}</div>
              </div>
              <div class="tp-input-wrap">
                <input
                  ref="typingInputRef"
                  v-model="typingInput"
                  class="tp-input"
                  :class="{ correct: typingResult === 'correct', wrong: typingResult === 'wrong' }"
                  placeholder="Nhập từ vựng..."
                  :disabled="!!typingResult"
                  @keydown.enter="checkTyping"
                />
                <button
                  v-if="!typingResult"
                  class="tp-submit"
                  :disabled="!typingInput.trim()"
                  @click="checkTyping"
                >
                  Kiểm tra
                </button>
              </div>
              <div v-if="typingResult" class="answer-result" :class="`result--${typingResult}`">
                {{ typingResult === 'correct' ? '✓ Chính xác!' : `✗ Đáp án đúng: ${currentWord.word}` }}
              </div>
              <button v-if="typingResult" class="btn-next" @click="nextWord">Tiếp theo →</button>
            </div>

            <!-- ── READING (fill context) ──────────────────────── -->
            <div v-else-if="currentMode === 'reading'" class="card-area">
              <div class="rd-question">
                <div class="rd-label">Hoàn thành câu sau:</div>
                <div class="rd-sentence" v-html="exampleWithInput"></div>
                <div class="rd-meaning">Nghĩa: {{ currentWord.meaning_vi }}</div>
              </div>
              <div class="tp-input-wrap">
                <input
                  ref="readingInputRef"
                  v-model="typingInput"
                  class="tp-input"
                  :class="{ correct: typingResult === 'correct', wrong: typingResult === 'wrong' }"
                  placeholder="Điền từ vào chỗ trống..."
                  :disabled="!!typingResult"
                  @keydown.enter="checkTyping"
                />
                <button
                  v-if="!typingResult"
                  class="tp-submit"
                  :disabled="!typingInput.trim()"
                  @click="checkTyping"
                >
                  Kiểm tra
                </button>
              </div>
              <div v-if="typingResult" class="answer-result" :class="`result--${typingResult}`">
                {{ typingResult === 'correct' ? '✓ Chính xác!' : `✗ Đáp án đúng: ${currentWord.word}` }}
              </div>
              <button v-if="typingResult" class="btn-next" @click="nextWord">Tiếp theo →</button>
            </div>

          </template>

          <!-- ── Empty queue ─────────────────────────────────────── -->
          <div v-else class="empty-study">
            <div class="empty-icon">📚</div>
            <div>Không có từ nào để luyện tập</div>
            <button class="btn-secondary" @click="$emit('close')">Đóng</button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  show:      { type: Boolean, default: false },
  words:     { type: Array,   default: () => [] },
  topicName: { type: String,  default: '' },
})

const emit = defineEmits(['close', 'mastery-updated'])

// ── Modes ────────────────────────────────────────────────────────────────────
const MODES = [
  {
    id: 'flashcard',
    label: 'Flashcard',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>`,
  },
  {
    id: 'multiple',
    label: 'Trắc nghiệm',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  },
  {
    id: 'typing',
    label: 'Gõ từ',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>`,
  },
  {
    id: 'reading',
    label: 'Đọc hiểu',
    icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  },
]

// ── Session state ─────────────────────────────────────────────────────────────
const currentMode    = ref('flashcard')
const queue          = ref([])   // shuffled list of words for this session
const queueIndex     = ref(0)
const doneCount      = ref(0)
const correctCount   = ref(0)
const completed      = ref(false)

// Flashcard
const cardFlipped    = ref(false)

// Multiple choice
const mcOptions      = ref([])
const selectedOption = ref(null)
const answered       = ref(false)
const lastCorrect    = ref(false)

// Typing / Reading
const typingInput    = ref('')
const typingResult   = ref(null)  // null | 'correct' | 'wrong'
const typingInputRef = ref(null)
const readingInputRef = ref(null)

// ── Computed ──────────────────────────────────────────────────────────────────
const currentWord = computed(() => queue.value[queueIndex.value] ?? null)

const progressPct = computed(() =>
  queue.value.length ? Math.round((doneCount.value / queue.value.length) * 100) : 0
)

/**
 * Example sentence with the target word replaced by underscores.
 * Used for the typing and reading modes.
 */
const exampleWithBlank = computed(() => {
  const w = currentWord.value
  if (!w?.example) return ''
  const re = new RegExp(`\\b${w.word}\\b`, 'gi')
  return w.example.replace(re, '_____')
})

/** Same but with a highlighted span so it looks like a fill-in-the-blank. */
const exampleWithInput = computed(() => {
  const w = currentWord.value
  if (!w?.example) return `<em>${w?.meaning_vi || ''}</em>`
  const re = new RegExp(`\\b${w.word}\\b`, 'gi')
  return w.example.replace(re, `<span class="blank">_____</span>`)
})

// ── Lifecycle ─────────────────────────────────────────────────────────────────
watch(
  () => props.show,
  (v) => { if (v) initSession() },
  { immediate: true }
)

function initSession() {
  const sorted = [...props.words].sort((a, b) => {
    // Prioritise: new → learning → mastered
    const order = { new: 0, learning: 1, mastered: 2 }
    return (order[a.mastery] ?? 0) - (order[b.mastery] ?? 0)
  })
  queue.value      = shuffle(sorted)
  queueIndex.value = 0
  doneCount.value  = 0
  correctCount.value = 0
  completed.value  = false
  resetCard()
}

function restartSession() {
  initSession()
}

function resetCard() {
  cardFlipped.value  = false
  mcOptions.value    = buildMcOptions()
  selectedOption.value = null
  answered.value     = false
  lastCorrect.value  = false
  typingInput.value  = ''
  typingResult.value = null
  if (currentMode.value === 'typing') {
    nextTick(() => typingInputRef.value?.focus())
  } else if (currentMode.value === 'reading') {
    nextTick(() => readingInputRef.value?.focus())
  }
}

// ── Actions ───────────────────────────────────────────────────────────────────

/** Flashcard: user says they know / don't know */
function markAnswer(correct) {
  correctCount.value += correct ? 1 : 0
  updateMastery(correct)
  doneCount.value++
  advanceQueue()
}

/** Multiple choice: select an option */
function selectMcOption(opt) {
  if (answered.value) return
  selectedOption.value = opt
  answered.value = true
  lastCorrect.value = opt.correct
  correctCount.value += opt.correct ? 1 : 0
  updateMastery(opt.correct)
  doneCount.value++
}

/** Typing: check if input matches the word (case-insensitive, trimmed) */
function checkTyping() {
  const w = currentWord.value
  if (!w || typingResult.value) return
  const isCorrect = typingInput.value.trim().toLowerCase() === w.word.toLowerCase()
  typingResult.value = isCorrect ? 'correct' : 'wrong'
  correctCount.value += isCorrect ? 1 : 0
  updateMastery(isCorrect)
  doneCount.value++
}

function nextWord() {
  advanceQueue()
}

function advanceQueue() {
  const next = queueIndex.value + 1
  if (next >= queue.value.length) {
    completed.value = true
    return
  }
  queueIndex.value = next
  resetCard()
}

// ── Mastery update ────────────────────────────────────────────────────────────
function updateMastery(correct) {
  const w = currentWord.value
  if (!w) return
  const next = computeNextMastery(w.mastery, correct)
  if (next !== w.mastery) {
    emit('mastery-updated', { wordId: w.id, topicId: w.topic_id, mastery: next })
  }
}

function computeNextMastery(current, correct) {
  if (correct) {
    if (current === 'new')      return 'learning'
    if (current === 'learning') return 'mastered'
    return 'mastered'
  } else {
    if (current === 'mastered') return 'learning'
    if (current === 'learning') return 'new'
    return 'new'
  }
}

// ── Multiple choice helpers ───────────────────────────────────────────────────
function buildMcOptions() {
  const w = currentWord.value
  if (!w) return []
  const correct = { text: w.meaning_vi || w.word, correct: true }
  const distractors = props.words
    .filter(x => x.id !== w.id && x.meaning_vi)
    .sort(() => Math.random() - 0.5)
    .slice(0, 3)
    .map(x => ({ text: x.meaning_vi, correct: false }))
  return shuffle([correct, ...distractors])
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}
</script>

<style scoped>
.study-overlay {
  position: fixed; inset: 0; z-index: 20000;
  background: rgba(0, 0, 0, .55);
  display: flex; align-items: center; justify-content: center; padding: 16px;
}

.study-box {
  background: #fff; border-radius: 24px; width: 100%; max-width: 520px;
  box-shadow: 0 32px 80px rgba(0,0,0,.22); overflow: hidden;
  display: flex; flex-direction: column;
  max-height: calc(100vh - 32px);
}

/* Header */
.study-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #f1f5f9;
}
.study-header__left {}
.study-title { font-size: 16px; font-weight: 800; color: #0f172a; }
.study-sub   { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.study-close {
  width: 32px; height: 32px; border-radius: 8px;
  background: none; border: none; cursor: pointer; color: #94a3b8;
  display: flex; align-items: center; justify-content: center; padding: 0;
}
.study-close:hover { background: #f1f5f9; color: #0f172a; }

/* Progress */
.study-progress-wrap {
  height: 4px; background: #e2e8f0; width: 100%;
}
.study-progress-bar {
  height: 4px; background: #34d399; transition: width .4s ease;
}

/* Mode tabs */
.mode-tabs {
  display: flex; gap: 4px; padding: 12px 16px 8px;
  flex-wrap: wrap;
}
.mode-tab {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 20px;
  border: 1.5px solid #e2e8f0; background: #f8fafc;
  color: #64748b; font-size: 12px; font-weight: 600; cursor: pointer;
  transition: all .15s;
}
.mode-tab:hover  { border-color: #34d399; color: #059669; }
.mode-tab.active { border-color: #15803d; background: #f0fdf4; color: #15803d; }

/* Card area */
.card-area {
  padding: 16px 20px 24px; flex: 1; overflow-y: auto;
  display: flex; flex-direction: column; gap: 16px;
}

/* ── FLASHCARD ── */
.flashcard {
  perspective: 1000px;
  cursor: pointer; border-radius: 16px;
  min-height: 200px; display: flex;
  position: relative;
  transform-style: preserve-3d;
  transition: transform .5s ease;
  border: 1.5px solid #e2e8f0;
  box-shadow: 0 4px 16px rgba(0,0,0,.06);
}
.flashcard.flipped { transform: rotateY(180deg); }

.flashcard-front, .flashcard-back {
  position: absolute; inset: 0;
  backface-visibility: hidden;
  border-radius: 16px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 24px; gap: 8px;
}
.flashcard-front { background: #fff; }
.flashcard-back  { background: #f0fdf4; transform: rotateY(180deg); }

.fc-word     { font-size: 32px; font-weight: 900; color: #0f172a; text-align: center; }
.fc-phonetic { font-size: 14px; color: #64748b; font-style: italic; }
.fc-type     { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #059669; background: #dcfce7; padding: 2px 10px; border-radius: 8px; }
.fc-hint     { font-size: 11px; color: #94a3b8; margin-top: 12px; }
.fc-meaning  { font-size: 22px; font-weight: 800; color: #15803d; text-align: center; }
.fc-example  { font-size: 13px; color: #475569; font-style: italic; text-align: center; margin-top: 4px; max-width: 100%; }

.fc-actions {
  display: flex; gap: 12px; justify-content: center;
}
.fc-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 28px; border-radius: 12px;
  border: none; font-size: 14px; font-weight: 700; cursor: pointer;
  transition: all .15s;
}
.fc-btn--wrong   { background: #fff1f2; color: #e11d48; border: 1.5px solid #fca5a5; }
.fc-btn--wrong:hover  { background: #e11d48; color: #fff; }
.fc-btn--correct { background: #f0fdf4; color: #059669; border: 1.5px solid #86efac; }
.fc-btn--correct:hover{ background: #059669; color: #fff; }
.fc-tip { text-align: center; font-size: 12px; color: #94a3b8; }

/* ── MULTIPLE CHOICE ── */
.mc-question {
  text-align: center; padding: 16px 0 4px;
}
.mc-word     { font-size: 28px; font-weight: 900; color: #0f172a; }
.mc-phonetic { font-size: 13px; color: #64748b; font-style: italic; margin-top: 4px; }
.mc-prompt   { font-size: 13px; color: #64748b; margin-top: 12px; }

.mc-options { display: flex; flex-direction: column; gap: 8px; }
.mc-option {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; border-radius: 12px;
  border: 1.5px solid #e2e8f0; background: #f8fafc;
  font-size: 13px; color: #374151; cursor: pointer; text-align: left;
  transition: all .15s; font-family: inherit;
}
.mc-option:hover:not(:disabled)  { border-color: #34d399; background: #f0fdf4; }
.mc-option.correct  { border-color: #059669; background: #dcfce7; color: #166534; }
.mc-option.wrong    { border-color: #e11d48; background: #fff1f2; color: #9f1239; }
.mc-option.disabled { opacity: .4; cursor: not-allowed; }
.mc-letter {
  width: 26px; height: 26px; border-radius: 6px;
  background: #e2e8f0; display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 12px; flex-shrink: 0; color: #475569;
}
.mc-option.correct .mc-letter { background: #059669; color: #fff; }
.mc-option.wrong   .mc-letter { background: #e11d48; color: #fff; }

/* ── TYPING / READING ── */
.tp-question, .rd-question { text-align: center; padding: 12px 0 4px; }
.tp-label, .rd-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #94a3b8; letter-spacing: .06em; }
.tp-meaning  { font-size: 24px; font-weight: 900; color: #15803d; margin-top: 8px; }
.tp-example  { font-size: 13px; color: #64748b; font-style: italic; margin-top: 6px; }
.rd-sentence { font-size: 16px; color: #0f172a; line-height: 1.7; margin-top: 10px; }
.rd-meaning  { font-size: 13px; color: #64748b; margin-top: 6px; }

.tp-input-wrap { display: flex; gap: 8px; }
.tp-input {
  flex: 1; padding: 10px 14px; border-radius: 12px;
  border: 1.5px solid #e2e8f0; font-size: 15px; font-family: inherit; outline: none;
  transition: border-color .15s;
}
.tp-input:focus { border-color: #34d399; }
.tp-input.correct { border-color: #059669; background: #f0fdf4; color: #166534; }
.tp-input.wrong   { border-color: #e11d48; background: #fff1f2; color: #9f1239; }
.tp-submit {
  padding: 10px 20px; border-radius: 12px; border: none;
  background: #34d399; color: #fff; font-size: 13px; font-weight: 700;
  cursor: pointer; transition: background .15s; white-space: nowrap;
}
.tp-submit:hover:not(:disabled) { background: #059669; }
.tp-submit:disabled { opacity: .4; cursor: not-allowed; }

/* Answer result */
.answer-result {
  padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 600; text-align: center;
}
.result--correct { background: #dcfce7; color: #166534; }
.result--wrong   { background: #fff1f2; color: #9f1239; }

.btn-next {
  align-self: flex-end; padding: 10px 24px; border-radius: 12px;
  background: #0f172a; color: #fff; border: none;
  font-size: 13px; font-weight: 700; cursor: pointer; transition: background .15s;
}
.btn-next:hover { background: #1e293b; }

/* Blank */
:deep(.blank) { display: inline-block; min-width: 60px; border-bottom: 2px solid #34d399; }

/* Done screen */
.done-screen {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 40px 20px;
}
.done-emoji  { font-size: 48px; }
.done-title  { font-size: 20px; font-weight: 800; color: #0f172a; }
.done-sub    { font-size: 14px; color: #64748b; }
.done-actions { display: flex; gap: 12px; margin-top: 8px; }

.btn-primary {
  padding: 10px 28px; border-radius: 12px; border: none;
  background: #34d399; color: #fff; font-size: 14px; font-weight: 700;
  cursor: pointer; transition: background .15s;
}
.btn-primary:hover { background: #059669; }
.btn-secondary {
  padding: 10px 24px; border-radius: 12px;
  border: 1.5px solid #e2e8f0; background: #f8fafc; color: #475569;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all .15s;
}
.btn-secondary:hover { border-color: #cbd5e1; background: #f1f5f9; }

/* Empty */
.empty-study {
  display: flex; flex-direction: column; align-items: center; gap: 16px;
  padding: 60px 20px; font-size: 14px; color: #64748b;
}
.empty-icon { font-size: 40px; }

/* Transition */
.study-fade-enter-active, .study-fade-leave-active { transition: opacity .2s, transform .2s; }
.study-fade-enter-from, .study-fade-leave-to { opacity: 0; transform: scale(.97); }
</style>

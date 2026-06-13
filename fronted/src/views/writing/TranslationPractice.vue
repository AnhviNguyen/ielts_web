<template>
  <div class="tp-layout" tabindex="-1" @keydown.ctrl.space.prevent="toggleAllHints">
    <!-- ══ LEFT SIDEBAR ══════════════════════════════════════════════ -->
    <aside class="tp-sidebar">
      <div class="sidebar-header">
        <button class="back-btn" @click="$router.back()" title="Quay lại">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
          </svg>
        </button>
        <div class="sidebar-meta">
          <p class="sidebar-meta__label">ĐỀ BÀI</p>
          <h2 class="sidebar-meta__title">{{ topicTitle }}</h2>
        </div>
      </div>

      <div class="sidebar-progress">
        <span>CÁC CÂU</span>
        <span>{{ currentIndex + 1 }} / {{ sentences.length }}</span>
      </div>

      <div class="sentence-list" ref="listRef">
        <button
          v-for="(sent, idx) in sentences"
          :key="sent.id"
          :class="['sentence-item', { 'sentence-item--active': idx === currentIndex }]"
          @click="selectSentence(idx)"
        >
          <span class="si-num">{{ idx + 1 }}</span>
          <span class="si-text">{{ preview(sent.vietnamese) }}</span>
          <span
            v-if="sent.last_score !== null"
            class="si-score"
            :class="scoreClass(sent.last_score)"
          >{{ sent.last_score }}</span>
        </button>
      </div>
    </aside>

    <!-- ══ RIGHT PANEL ════════════════════════════════════════════════ -->
    <main class="tp-main" v-if="current">
      <!-- Direction header -->
      <div class="direction-bar">
        <span class="dir-badge">VN</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 8l4 4m0 0l-4 4m4-4H3"/>
        </svg>
        <span class="dir-label">TIẾNG VIỆT → ENGLISH</span>
      </div>

      <!-- Vietnamese sentence -->
      <p class="vi-sentence">{{ current.vietnamese }}</p>

      <!-- ── Hint words section ─────────────────────────────────── -->
      <div class="hint-section">
        <div class="hint-section__header">
          <div class="hint-section__title">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            GỢI Ý TỪ
          </div>
          <button class="toggle-all-btn" @click="toggleAllHints">
            <svg v-if="!allRevealed" xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
            {{ allRevealed ? 'Ẩn tất cả' : 'Hiện tất cả' }}
          </button>
        </div>

        <div class="hint-chips">
          <button
            v-for="(hint, i) in hints"
            :key="i"
            :class="['hint-chip', { 'hint-chip--revealed': isRevealed(i) }]"
            @click="revealWord(i)"
          >
            <span class="hint-chip__text">{{ isRevealed(i) ? hint.raw : hint.masked }}</span>
          </button>
        </div>
      </div>

      <!-- Grammar note -->
      <div class="grammar-row">
        <button class="grammar-btn" @click="showExplain = !showExplain">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Xem gợi ý ngữ pháp
        </button>
      </div>

      <Transition name="expand">
        <div v-if="showExplain && current.explanation" class="grammar-note">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; margin-top:1px">
            <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M12 8v4"/><path d="M12 16h.01"/>
          </svg>
          <p>{{ current.explanation }}</p>
        </div>
      </Transition>

      <!-- ── Translation input ───────────────────────────────────── -->
      <div class="input-section">
        <label class="input-label">BÀI DỊCH CỦA EM</label>
        <textarea
          ref="textareaRef"
          v-model="userTranslation"
          class="translation-textarea"
          placeholder="Nhập bản dịch tiếng Anh của bạn vào đây..."
          :disabled="submitted"
          @keydown.enter.exact.prevent="handleEnterKey"
        ></textarea>
        <p v-if="submitError" class="submit-error">{{ submitError }}</p>
      </div>

      <!-- ── Result ─────────────────────────────────────────────── -->
      <Transition name="slide-up">
        <div v-if="result" class="result-panel">
          <div class="result-score" :class="scoreClass(result.score)">
            <span class="rs-num">{{ result.score }}</span>
            <span class="rs-max">/10</span>
          </div>
          <div class="result-detail">
            <p class="result-feedback">{{ result.feedback }}</p>
            <div v-if="showCorrection" class="correction-block">
              <p class="correction-block__label">
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                Cách sửa đúng
              </p>
              <p class="correction-block__text">{{ result.correction }}</p>
            </div>
            <div class="model-answer">
              <p class="model-answer__label">
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Đáp án mẫu
              </p>
              <p class="model-answer__text">{{ result.model_answer }}</p>
            </div>
          </div>
        </div>
      </Transition>

      <!-- ── Actions ────────────────────────────────────────────── -->
      <div class="tp-actions">
        <button
          v-if="!submitted"
          class="btn-submit"
          :disabled="!canSubmit || submitting"
          @click="submitTranslation"
        >
          <span v-if="submitting" class="spinner"></span>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
          {{ submitting ? 'Đang chấm…' : 'Nộp bài  (Enter)' }}
        </button>

        <template v-if="submitted">
          <button class="btn-retry" @click="retryThis">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/>
            </svg>
            Thử lại
          </button>
          <button
            class="btn-next"
            :disabled="currentIndex >= sentences.length - 1"
            @click="nextSentence"
          >
            Câu tiếp
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </template>
      </div>

      <p class="keyboard-hint">
        <kbd>Ctrl</kbd> + <kbd>Space</kbd> mở/ẩn từ &nbsp;·&nbsp;
        <kbd>Enter</kbd> nộp bài
      </p>
    </main>

    <!-- Loading placeholder -->
    <div v-else-if="loading" class="tp-loading-main">
      <div class="loading-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchSentences, checkTranslation } from '@/services/translationService.js'

const route  = useRoute()
const router = useRouter()

const topicId    = computed(() => Number(route.params.topicId))
const topicTitle = ref('Luyện dịch')
const sentences  = ref([])
const loading    = ref(true)

const currentIndex     = ref(0)
const current          = computed(() => sentences.value[currentIndex.value] ?? null)
const hints            = computed(() => current.value?.hint_words ?? [])
const revealedSet      = ref(new Set())
const allRevealed      = ref(false)
const userTranslation  = ref('')
const submitting       = ref(false)
const submitted        = ref(false)
const result           = ref(null)
const submitError      = ref('')
const showExplain      = ref(false)
const showCorrection   = computed(() => {
  if (!result.value?.correction) return false
  const corr = result.value.correction.trim().toLowerCase()
  const user = userTranslation.value.trim().toLowerCase()
  return corr !== user
})
const textareaRef      = ref(null)
const listRef          = ref(null)

const MIN_TRANSLATION_LEN = 3

const canSubmit = computed(() => userTranslation.value.trim().length >= MIN_TRANSLATION_LEN)

function formatSubmitError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || d.loc?.join('.') || String(d)).join('; ')
  }
  if (err?.response?.status === 422) {
    return 'Bản dịch quá ngắn hoặc không hợp lệ (tối thiểu 3 ký tự).'
  }
  return err?.message || 'Không thể kết nối AI. Vui lòng thử lại.'
}

// ── Load ──────────────────────────────────────────────────────────────────────

async function load() {
  loading.value = true
  try {
    sentences.value = await fetchSentences(topicId.value)
    resetState()
  } finally {
    loading.value = false
    await nextTick()
    textareaRef.value?.focus()
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────

function selectSentence(idx) {
  currentIndex.value = idx
  resetState()
  scrollToActive()
  nextTick(() => textareaRef.value?.focus())
}

function nextSentence() {
  if (currentIndex.value < sentences.value.length - 1) {
    selectSentence(currentIndex.value + 1)
  }
}

// ── Hints ─────────────────────────────────────────────────────────────────────

function isRevealed(i) {
  return allRevealed.value || revealedSet.value.has(i)
}

function revealWord(i) {
  const s = new Set(revealedSet.value)
  s.has(i) ? s.delete(i) : s.add(i)
  revealedSet.value = s
}

function toggleAllHints() {
  allRevealed.value = !allRevealed.value
}

// ── Submit ────────────────────────────────────────────────────────────────────

async function submitTranslation() {
  const text = userTranslation.value.trim()
  if (!text || submitting.value || submitted.value) return
  if (text.length < MIN_TRANSLATION_LEN) {
    submitError.value = `Bản dịch cần ít nhất ${MIN_TRANSLATION_LEN} ký tự.`
    return
  }
  if (!current.value?.id) {
    submitError.value = 'Không tìm thấy câu cần dịch. Tải lại trang và thử lại.'
    return
  }
  submitting.value = true
  submitError.value = ''
  try {
    result.value  = await checkTranslation(current.value.id, text)
    submitted.value = true
    sentences.value[currentIndex.value].last_score = result.value.score
  } catch (err) {
    submitError.value = formatSubmitError(err)
  } finally {
    submitting.value = false
  }
}

function handleEnterKey() {
  if (!submitted.value) submitTranslation()
  else nextSentence()
}

function retryThis() {
  userTranslation.value = ''
  result.value          = null
  submitted.value       = false
  showExplain.value     = false
  revealedSet.value     = new Set()
  allRevealed.value     = false
  nextTick(() => textareaRef.value?.focus())
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function resetState() {
  userTranslation.value = ''
  result.value          = null
  submitError.value     = ''
  submitted.value       = false
  submitting.value      = false
  showExplain.value     = false
  revealedSet.value     = new Set()
  allRevealed.value     = false
}

function preview(text) {
  return text.length > 50 ? text.slice(0, 50) + '…' : text
}

function scoreClass(score) {
  if (score == null) return ''
  if (score >= 8)   return 'score--high'
  if (score >= 5.5) return 'score--mid'
  return 'score--low'
}

function scrollToActive() {
  nextTick(() => {
    const el = listRef.value?.querySelector('.sentence-item--active')
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

onMounted(load)
watch(topicId, load)
</script>

<style scoped>
/* ══ Layout ═══════════════════════════════════════════════════════════════════ */
.tp-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  height: calc(100vh - 60px);
  overflow: hidden;
  background: var(--bg-base);
}

/* ══ Sidebar ══════════════════════════════════════════════════════════════════ */
.tp-sidebar {
  display: flex;
  flex-direction: column;
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 18px 14px 12px;
  border-bottom: 1px solid var(--border);
}

.back-btn {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  margin-top: 2px;
  border-radius: 8px;
  border: 1.5px solid var(--border);
  background: var(--bg-interactive);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--ink2);
  transition: all 0.15s;
}

.back-btn:hover { border-color: var(--spotify-green); color: var(--spotify-green); background: var(--green-bg); }

.sidebar-meta__label {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--ink3);
  margin-bottom: 3px;
}

.sidebar-meta__title {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-emphasis);
  line-height: 1.3;
}

.sidebar-progress {
  display: flex;
  justify-content: space-between;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink3);
  padding: 8px 14px;
}

.sentence-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 6px 16px;
}

.sentence-item {
  width: 100%;
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  margin-bottom: 1px;
  transition: background 0.12s;
}

.sentence-item:hover { background: var(--bg-interactive); }

.sentence-item--active {
  background: var(--green-bg);
  box-shadow: inset 3px 0 0 var(--spotify-green);
}

.si-num {
  flex-shrink: 0;
  width: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--ink3);
}

.sentence-item--active .si-num { color: var(--spotify-green); }

.si-text {
  flex: 1;
  font-size: 0.81rem;
  color: var(--ink2);
  line-height: 1.4;
  word-break: break-word;
}

.sentence-item--active .si-text { color: var(--text-emphasis); font-weight: 500; }

.si-score {
  flex-shrink: 0;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 8px;
}

/* ══ Main ═════════════════════════════════════════════════════════════════════ */
.tp-main {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 36px 52px 48px;
  gap: 0;
}

/* Direction bar */
.direction-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
}

.dir-badge {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  padding: 3px 8px;
  border-radius: 6px;
  background: var(--green-bg);
  color: var(--spotify-green);
}

.dir-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--ink2);
}

/* Vietnamese sentence */
.vi-sentence {
  font-size: 1.55rem;
  font-weight: 700;
  color: var(--text-emphasis);
  line-height: 1.5;
  margin-bottom: 28px;
}

/* ══ Hint section ════════════════════════════════════════════════════════════ */
.hint-section {
  margin-bottom: 16px;
  padding: 18px 20px;
  border-radius: 14px;
  border: 1.5px solid var(--border);
  background: var(--bg-surface);
}

.hint-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.hint-section__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink2);
}

.toggle-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--spotify-green);
  background: none;
  border: 1px solid var(--spotify-green);
  border-radius: 20px;
  padding: 4px 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.toggle-all-btn:hover { background: var(--green-bg); }

/* Hint chips */
.hint-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hint-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  padding: 8px 16px;
  border-radius: 24px;
  border: 1.5px solid var(--border);
  background: var(--bg-interactive);
  cursor: pointer;
  transition: all 0.15s;
}

.hint-chip:hover {
  border-color: var(--spotify-green);
  background: var(--green-bg);
}

.hint-chip__text {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--ink2);
  font-family: 'Courier New', 'Consolas', monospace;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.hint-chip--revealed {
  background: var(--green-bg);
  border-color: var(--spotify-green);
}

.hint-chip--revealed .hint-chip__text {
  color: var(--spotify-green);
  font-family: inherit;
  letter-spacing: 0;
}

/* ══ Grammar note ════════════════════════════════════════════════════════════ */
.grammar-row { margin-bottom: 12px; }

.grammar-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--spotify-green);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}

.grammar-btn:hover { color: var(--spotify-green-dark); }

.grammar-note {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 10px;
  border-left: 3px solid var(--spotify-green);
  background: var(--green-bg);
  margin-bottom: 16px;
  font-size: 0.875rem;
  color: var(--ink2);
  line-height: 1.6;
}

/* ══ Input section ════════════════════════════════════════════════════════════ */
.input-section { margin-bottom: 20px; }

.input-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink3);
  margin-bottom: 10px;
}

.translation-textarea {
  width: 100%;
  min-height: 140px;
  padding: 18px 20px;
  border-radius: 14px;
  border: 1.5px solid var(--border);
  background: var(--bg-surface);
  font-size: 1rem;
  color: var(--text-emphasis);
  resize: vertical;
  line-height: 1.7;
  transition: border-color 0.15s, box-shadow 0.15s;
  font-family: inherit;
  box-sizing: border-box;
}

.translation-textarea:focus {
  outline: none;
  border-color: var(--spotify-green);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.15);
}

.translation-textarea:disabled {
  opacity: 0.65;
  cursor: default;
  background: var(--bg-interactive);
}

.translation-textarea::placeholder { color: var(--ink3); }

.submit-error {
  margin-top: 8px;
  font-size: 0.82rem;
  color: var(--rose);
  line-height: 1.5;
}

/* ══ Result panel ════════════════════════════════════════════════════════════ */
.result-panel {
  display: flex;
  gap: 18px;
  align-items: flex-start;
  padding: 20px;
  border-radius: 14px;
  border: 1.5px solid var(--border);
  background: var(--bg-surface);
  margin-bottom: 20px;
}

.result-score {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  min-width: 68px;
}

.rs-num {
  font-size: 2rem;
  font-weight: 900;
  line-height: 1;
}

.rs-max {
  font-size: 0.75rem;
  font-weight: 600;
  opacity: 0.6;
}

.result-detail { flex: 1; }

.result-feedback {
  font-size: 0.9rem;
  color: var(--ink2);
  line-height: 1.65;
  margin-bottom: 14px;
}

.correction-block {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--amber);
  background: var(--amber-bg);
}

.correction-block__label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--amber);
  margin-bottom: 5px;
}

.correction-block__text {
  font-size: 0.92rem;
  color: var(--ink2);
  line-height: 1.6;
}

.model-answer__label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ink3);
  margin-bottom: 5px;
}

.model-answer__text {
  font-size: 0.92rem;
  color: var(--text-emphasis);
  font-style: italic;
  line-height: 1.6;
}

/* Score color states */
.score--high { background: #dcfce7; }
.score--high .rs-num { color: #166534; }
.score--mid  { background: #fef9c3; }
.score--mid  .rs-num { color: #854d0e; }
.score--low  { background: #fee2e2; }
.score--low  .rs-num { color: #991b1b; }

/* Score badge in sidebar */
.si-score.score--high { background: #dcfce7; color: #166534; }
.si-score.score--mid  { background: #fef9c3; color: #854d0e; }
.si-score.score--low  { background: #fee2e2; color: #991b1b; }

/* ══ Actions ═════════════════════════════════════════════════════════════════ */
.tp-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}

.btn-submit {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 15px 24px;
  border-radius: 12px;
  border: none;
  background: var(--spotify-green);
  color: #000;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-submit:hover:not(:disabled) { background: var(--spotify-green-dark); }
.btn-submit:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-retry, .btn-next {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 20px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-retry {
  border: 1.5px solid #e5e7eb;
  background: #fff;
  color: #374151;
}

.btn-retry:hover { border-color: #34d399; color: #059669; }

.btn-next {
  border: none;
  background: #34d399;
  color: #064e3b;
}

.btn-next:hover:not(:disabled) { background: #10b981; }
.btn-next:disabled { opacity: 0.4; cursor: not-allowed; }

/* ══ Keyboard hint ═══════════════════════════════════════════════════════════ */
.keyboard-hint {
  font-size: 0.73rem;
  color: #d1d5db;
  text-align: center;
}

kbd {
  display: inline-block;
  padding: 1px 5px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 0.68rem;
  background: #f9fafb;
  color: #6b7280;
  font-family: inherit;
}

/* ══ Transitions ═════════════════════════════════════════════════════════════ */
.slide-up-enter-active { transition: all 0.28s ease; }
.slide-up-enter-from   { opacity: 0; transform: translateY(10px); }

.expand-enter-active, .expand-leave-active { transition: all 0.2s ease; }
.expand-enter-from, .expand-leave-to       { opacity: 0; max-height: 0; margin: 0; padding: 0; }

/* ══ Loading ══════════════════════════════════════════════════════════════════ */
.tp-loading-main {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.loading-dots {
  display: flex;
  gap: 8px;
}

.loading-dots span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #34d399;
  animation: bounce 1.2s infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 100% { transform: translateY(0); opacity: 0.5; }
  50%       { transform: translateY(-8px); opacity: 1; }
}

/* ══ Spinner ══════════════════════════════════════════════════════════════════ */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ══ Responsive ══════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .tp-layout {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .tp-sidebar {
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
    max-height: 200px;
  }

  .tp-main { padding: 24px 20px 40px; }
  .vi-sentence { font-size: 1.25rem; }
}
</style>

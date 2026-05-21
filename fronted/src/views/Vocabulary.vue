<template>
  <div class="vocab-page">

    <!-- ── Page header ──────────────────────────────────────────────────── -->
    <div class="vocab-header">
      <div>
        <div class="vocab-header__title">Từ vựng của tôi</div>
        <div class="vocab-header__sub">Lặp lại ngắt quãng · quản lý từ theo topic</div>
      </div>
      <div class="vocab-header__stats">
        <div class="stat-pill stat-pill--green">
          <span class="stat-num">{{ totalWords }}</span>
          <span class="stat-lbl">Tổng từ</span>
        </div>
        <div class="stat-pill">
          <span class="stat-num">{{ masteredCount }}</span>
          <span class="stat-lbl">Đã thuộc</span>
        </div>
        <div class="stat-pill stat-pill--amber">
          <span class="stat-num">{{ newCount }}</span>
          <span class="stat-lbl">Chưa thuộc</span>
        </div>
      </div>
    </div>

    <!-- ── Main layout ───────────────────────────────────────────────────── -->
    <div
      ref="splitContainerRef"
      class="vocab-layout"
      :class="{
        'vocab-layout--study': viewTab === 'study',
        'vocab-layout--resizing': isSplitResizing,
      }"
    >

      <!-- Left: topic sidebar -->
      <aside
        class="vocab-sidebar"
        :style="viewTab === 'study' ? studySidebarStyle : undefined"
      >
        <div class="sidebar-header">
          <span class="sidebar-title">Topic của tôi</span>
          <button class="sidebar-add-btn" @click="showAddTopic = true" title="Thêm topic">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
        </div>

        <div v-if="topicsLoading" class="sidebar-loading">Đang tải...</div>
        <div v-else-if="topicsError" class="sidebar-empty sidebar-error">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:6px;color:#e11d48"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {{ topicsError }}
          <button class="link-btn" style="margin-top:8px" @click="retryLoad()">Thử lại</button>
        </div>
        <div v-else-if="!topics.length" class="sidebar-empty">
          Chưa có topic nào.<br>
          <button class="link-btn" @click="showAddTopic = true">Tạo topic đầu tiên</button>
        </div>
        <div v-else class="topic-list">
          <div
            v-for="t in topics"
            :key="t.id"
            class="topic-item"
            :class="{ active: selectedTopicId === t.id }"
            @click="onSelectTopic(t.id)"
          >
            <div class="topic-item__body">
              <span class="topic-item__name">{{ t.name }}</span>
              <span class="topic-item__count">{{ t.word_count }} từ</span>
            </div>
            <!-- Context menu trigger -->
            <div class="topic-item__menu" @click.stop>
              <button class="menu-btn" @click.stop="openTopicMenu($event, t)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="1" fill="currentColor"/><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="19" r="1" fill="currentColor"/></svg>
              </button>
            </div>
          </div>
        </div>
      </aside>

      <div
        v-if="viewTab === 'study'"
        class="split-handle"
        role="separator"
        aria-orientation="vertical"
        aria-label="Kéo để điều chỉnh chiều rộng topic và luyện tập"
        title="Kéo để chỉnh chiều rộng"
        @mousedown="startSplitResize"
      />

      <!-- Right: topic content -->
      <main
        class="vocab-main"
        :class="{ 'vocab-main--study': viewTab === 'study' }"
        :style="viewTab === 'study' ? studyMainStyle : undefined"
      >
        <template v-if="topics.length">
          <div class="main-header">
            <div>
              <div class="main-title">
                {{ viewTab === 'study' ? 'Luyện tập hôm nay' : (selectedTopic?.name || 'Quản lý từ') }}
              </div>
              <div class="main-sub">
                <template v-if="viewTab === 'study'">Lặp lại ngắt quãng · từ đến hạn ôn</template>
                <template v-else-if="selectedTopicId">
                  {{ filteredWords.length }}<template v-if="wordSearch"> / {{ words.length }}</template> từ vựng
                </template>
                <template v-else>Chọn topic bên trái để quản lý từ</template>
              </div>
            </div>
            <div class="main-header-actions">
              <div class="view-tabs">
                <button
                  type="button"
                  class="view-tab"
                  :class="{ active: viewTab === 'study' }"
                  @click="viewTab = 'study'"
                >Luyện tập</button>
                <button
                  type="button"
                  class="view-tab"
                  :class="{ active: viewTab === 'manage' }"
                  @click="viewTab = 'manage'"
                >Quản lý từ</button>
              </div>
              <div v-if="viewTab === 'manage' && selectedTopicId" class="word-search-wrap">
                <svg class="word-search-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input v-model="wordSearch" class="word-search-input" placeholder="Tìm từ..." />
                <button v-if="wordSearch" class="word-search-clear" @click="wordSearch = ''">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
              <button v-if="viewTab === 'manage' && selectedTopicId" class="add-word-btn" @click="showAddWord = true">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Thêm từ
              </button>
            </div>
          </div>

          <VocabDueList v-if="viewTab === 'study'" ref="dueListRef" :topics="topics" />

          <!-- Word table (manage tab) -->
          <template v-if="viewTab === 'manage' && selectedTopicId">
          <div v-if="wordsLoading" class="empty-state">Đang tải...</div>
          <div v-else-if="!words.length" class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
            <div class="empty-title">Topic chưa có từ nào</div>
            <button class="add-word-btn" @click="showAddWord = true">Thêm từ đầu tiên</button>
          </div>

          <div v-else-if="!filteredWords.length && wordSearch" class="empty-state">
            <div class="empty-title">Không tìm thấy "{{ wordSearch }}"</div>
            <button class="link-btn" @click="wordSearch = ''">Xóa tìm kiếm</button>
          </div>

          <div v-else class="word-table">
            <div class="word-table-head">
              <div class="th w-24">Trạng thái</div>
              <div class="th w-24 hidden lg:block">SRS</div>
              <div class="th flex-1">Tiếng Anh</div>
              <div class="th w-28 hidden sm:block">Phát âm</div>
              <div class="th flex-1">Tiếng Việt</div>
              <div class="th flex-[2] hidden md:block">Ví dụ (EN)</div>
              <div class="th w-20">Thao tác</div>
            </div>

            <div
              v-for="w in filteredWords"
              :key="w.id"
              class="word-row"
            >
              <div class="td w-24">
                <select
                  :value="w.mastery"
                  class="mastery-select"
                  :class="`mastery--${w.mastery}`"
                  @change="updateMastery(w, $event.target.value)"
                >
                  <option value="new">Chưa thuộc</option>
                  <option value="learning">Nhớ sơ sơ</option>
                  <option value="mastered">Đã thuộc</option>
                </select>
              </div>
              <div class="td w-24 hidden lg:block">
                <div class="srs-cell">
                  <span v-if="isDue(w)" class="srs-due">Đến hạn</span>
                  <span v-else class="srs-ok">{{ formatSrsNext(w) }}</span>
                  <span class="srs-meta">{{ w.srs_interval_days ?? 0 }}d · rep {{ w.srs_repetitions ?? 0 }}</span>
                </div>
              </div>
              <div class="td flex-1">
                <div class="word-cell">
                  <span class="word-text">{{ w.word }}</span>
                  <button class="tts-btn" @click="speak(w.word)" title="Phát âm">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                  </button>
                  <!-- Badge showing where the word was saved from -->
                  <span v-if="sourceLabel(w)" class="source-badge" :class="`source-badge--${w.source_type}`">
                    {{ sourceLabel(w) }}
                  </span>
                </div>
                <div v-if="w.phonetic" class="word-phonetic">/ {{ w.phonetic }} /</div>
                <div v-if="w.word_type" class="word-type-pill">{{ w.word_type }}</div>
              </div>
              <div class="td w-28 hidden sm:block">
                <span class="word-phonetic block">{{ w.phonetic ? `/ ${w.phonetic} /` : '—' }}</span>
              </div>
              <div class="td flex-1">
                <span class="meaning-vi">{{ w.meaning_vi || '—' }}</span>
              </div>
              <div class="td flex-[2] hidden md:block">
                <span class="example-text">{{ w.example || '—' }}</span>
              </div>
              <!-- Actions -->
              <div class="td w-20">
                <div class="row-actions">
                  <button class="row-action-btn" @click="editWord(w)" title="Sửa">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                  </button>
                  <button class="row-action-btn row-action-btn--del" @click="deleteWord(w)" title="Xoá">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
          </template>

          <div v-else-if="viewTab === 'manage'" class="empty-state">
            <div class="empty-title">Chọn một topic để quản lý từ vựng</div>
          </div>
        </template>

        <!-- No topics at all -->
        <div v-else class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          <div class="empty-title">Chọn một topic để xem từ vựng</div>
        </div>
      </main>
    </div>

    <!-- ── Add/Edit Topic modal ───────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showAddTopic || editingTopic" class="modal-overlay" @click.self="cancelTopicModal">
          <div class="modal-sm">
            <div class="modal-sm-header">
              <span>{{ editingTopic ? 'Đổi tên topic' : 'Tạo topic mới' }}</span>
              <button @click="cancelTopicModal"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
            </div>
            <div class="modal-sm-body">
              <input
                ref="topicInputRef"
                v-model="topicName"
                class="topic-input"
                placeholder="Tên topic..."
                @keydown.enter="saveTopicModal"
              />
            </div>
            <div class="modal-sm-footer">
              <button class="btn-cancel" @click="cancelTopicModal">Hủy</button>
              <button class="btn-green" @click="saveTopicModal">Lưu</button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Add/Edit Word modal -->
      <Transition name="modal-fade">
        <div v-if="showAddWord || editingWord" class="modal-overlay" @click.self="cancelWordModal">
          <div class="modal-lg">
            <div class="modal-sm-header">
              <span>{{ editingWord ? 'Chỉnh sửa từ vựng' : 'Thêm từ vựng mới' }}</span>
              <button @click="cancelWordModal"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
            </div>
            <div class="modal-lg-body">
              <div class="field-grid">
                <div class="field">
                  <label>Tiếng Anh *</label>
                  <input v-model="wordForm.word" placeholder="e.g. perseverance" />
                </div>
                <div class="field">
                  <label>Phát âm (IPA)</label>
                  <input v-model="wordForm.phonetic" placeholder="ˌpɜː.sɪˈvɪər.əns" />
                </div>
                <div class="field">
                  <label>Loại từ</label>
                  <input v-model="wordForm.word_type" placeholder="noun / verb / phrase..." />
                </div>
                <div class="field col-span-2">
                  <label>Nghĩa tiếng Anh</label>
                  <textarea v-model="wordForm.meaning_en" rows="2" placeholder="continued effort despite difficulties" />
                </div>
                <div class="field">
                  <label>Tiếng Việt (nghĩa)</label>
                  <input v-model="wordForm.meaning_vi" placeholder="sự kiên trì, bền bỉ" />
                </div>
                <div class="field col-span-2">
                  <label>Ví dụ tiếng Anh</label>
                  <textarea v-model="wordForm.example" rows="2" placeholder="His perseverance led to success." />
                </div>
                <div class="field col-span-2">
                  <label>Ví dụ tiếng Việt (tuỳ chọn)</label>
                  <textarea v-model="wordForm.example_vi" rows="2" placeholder="Sự kiên trì của anh ấy..." />
                </div>
                <div class="field col-span-2">
                  <label>Ghi chú</label>
                  <textarea v-model="wordForm.note" rows="2" placeholder="Ghi chú cá nhân..." />
                </div>
              </div>
            </div>
            <div class="modal-sm-footer">
              <button class="btn-cancel" @click="cancelWordModal">Hủy</button>
              <button class="btn-green" :disabled="!wordForm.word.trim()" @click="saveWordModal">Lưu</button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Topic context menu — positioned near the trigger button -->
      <Transition name="popup-fade">
        <div
          v-if="topicMenu.visible"
          class="topic-ctx-menu"
          :style="{ left: topicMenu.x + 'px', top: topicMenu.y + 'px' }"
          @click.stop
        >
          <button @click="startRenameTopic">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Đổi tên
          </button>
          <button class="danger" @click="confirmDeleteTopic">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            Xóa topic
          </button>
        </div>
      </Transition>

    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useVocabulary } from '@/composables/useVocabulary.js'
import { useSplitPane } from '@/composables/useSplitPane.js'
import VocabDueList from '@/components/vocabulary/VocabDueList.vue'

const {
  topics, topicsLoading, topicsError,
  words, wordsLoading, selectedTopicId, selectedTopic,
  stats,
  loadTopics, selectTopic, addTopic, renameTopic, removeTopic,
  addWord, patchWord, removeWord, refreshStats, init,
} = useVocabulary()

const viewTab = ref('study')

const {
  containerRef: splitContainerRef,
  isResizing: isSplitResizing,
  startResize: startSplitResize,
  startPaneStyle: studySidebarStyle,
  endPaneStyle: studyMainStyle,
} = useSplitPane({
  storageKey: 'vocab-study-split-pct',
  defaultPct: 33.33,
  minPct: 20,
  maxPct: 50,
})

const showAddTopic = ref(false)
const editingTopic = ref(null)
const topicName    = ref('')

const showAddWord  = ref(false)
const editingWord  = ref(null)
const wordForm     = ref(emptyWordForm())

const topicMenu    = ref({ visible: false, topic: null, x: 0, y: 0 })
const wordSearch   = ref('')
const topicInputRef = ref(null)

const dueListRef = ref(null)

async function onSelectTopic(id) {
  wordSearch.value = ''
  await selectTopic(id)
}

function isDue(w) {
  if (!w.srs_next_review_at) return true
  return new Date(w.srs_next_review_at) <= new Date()
}

function formatSrsNext(w) {
  if (!w.srs_next_review_at) return 'Mới'
  const d = new Date(w.srs_next_review_at)
  const now = new Date()
  if (d <= now) return 'Hôm nay'
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}

// Auto-focus topic name input when the modal opens
watch([showAddTopic, editingTopic], ([showAdd, editT]) => {
  if (showAdd || editT) {
    nextTick(() => topicInputRef.value?.focus())
  }
})

const totalWords    = computed(() => stats.value.total)
const masteredCount = computed(() => stats.value.mastered)
const newCount      = computed(() => stats.value.new)

const filteredWords = computed(() => {
  if (!wordSearch.value.trim()) return words.value
  const q = wordSearch.value.toLowerCase()
  return words.value.filter(w =>
    w.word.toLowerCase().includes(q) ||
    (w.meaning_vi || '').toLowerCase().includes(q) ||
    (w.example || '').toLowerCase().includes(q) ||
    (w.note || '').toLowerCase().includes(q)
  )
})

// ── Init ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  window.addEventListener('click', closeTopicMenu)
  try {
    await init()
  } catch (err) {
    console.error('[Vocabulary] init error:', err?.message || err)
  }
})
onUnmounted(() => window.removeEventListener('click', closeTopicMenu))

// ── Retry after error ─────────────────────────────────────────────────────────
async function retryLoad() {
  try {
    await init()
  } catch { /* topicsError set in composable */ }
}

function cancelTopicModal() {
  showAddTopic.value = false
  editingTopic.value = null
  topicName.value = ''
}

async function saveTopicModal() {
  const name = topicName.value.trim()
  if (!name) return
  if (editingTopic.value) {
    await renameTopic(editingTopic.value.id, name)
  } else {
    await addTopic(name)
    viewTab.value = 'study'
  }
  cancelTopicModal()
}

/** Open context menu anchored to the button that was clicked. */
function openTopicMenu(event, topic) {
  const btn = event.currentTarget
  const rect = btn.getBoundingClientRect()
  topicMenu.value = {
    visible: true,
    topic,
    x: rect.right - 140,  // align right edge of menu with button
    y: rect.bottom + 4,
  }
  event.stopPropagation()
}

function closeTopicMenu() {
  topicMenu.value.visible = false
}

function startRenameTopic() {
  editingTopic.value = topicMenu.value.topic
  topicName.value    = topicMenu.value.topic.name
  topicMenu.value.visible = false
}

async function confirmDeleteTopic() {
  const t = topicMenu.value.topic
  topicMenu.value.visible = false
  if (!confirm(`Xóa topic "${t.name}" và toàn bộ từ vựng?`)) return
  await removeTopic(t.id)
}

// ── Words ─────────────────────────────────────────────────────────────────────
function emptyWordForm() {
  return { word: '', phonetic: '', word_type: '', meaning_en: '', meaning_vi: '', example: '', example_vi: '', note: '' }
}

function editWord(w) {
  editingWord.value = w
  wordForm.value = {
    word: w.word, phonetic: w.phonetic || '', word_type: w.word_type || '',
    meaning_en: w.meaning_en || '', meaning_vi: w.meaning_vi || '',
    example: w.example || '', example_vi: w.example_vi || '', note: w.note || '',
  }
}

function cancelWordModal() {
  showAddWord.value  = false
  editingWord.value  = null
  wordForm.value     = emptyWordForm()
}

async function saveWordModal() {
  if (!wordForm.value.word.trim() || !selectedTopicId.value) return
  if (editingWord.value) {
    await patchWord(selectedTopicId.value, editingWord.value.id, wordForm.value)
  } else {
    await addWord(selectedTopicId.value, wordForm.value)
  }
  cancelWordModal()
}

async function deleteWord(w) {
  if (!confirm(`Xóa từ "${w.word}"?`)) return
  await removeWord(selectedTopicId.value, w.id)
}

async function updateMastery(w, mastery) {
  await patchWord(selectedTopicId.value, w.id, { mastery })
  w.mastery = mastery
}

function speak(word) {
  if (!word || !window.speechSynthesis) return
  const utt = new SpeechSynthesisUtterance(word)
  utt.lang = 'en-US'; utt.rate = 0.9
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(utt)
}

/** Label for word provenance badge. */
function sourceLabel(w) {
  if (w.source_type === 'reading')   return 'Reading'
  if (w.source_type === 'listening') return 'Listening'
  return null
}
</script>

<style scoped>
/* ── Layout ────────────────────────────────────────────────────────────── */
.vocab-page {
  min-height: 100vh;
  background: #fff;
  padding: 24px 24px 48px;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.vocab-header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: #fff; border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.vocab-header__title { font-size: 20px; font-weight: 800; color: #0f172a; }
.vocab-header__sub   { font-size: 13px; color: #64748b; margin-top: 2px; }
.vocab-header__stats { display: flex; gap: 10px; flex-wrap: wrap; }

.stat-pill {
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 16px; border-radius: 10px;
  border: 1.5px solid #e2e8f0; background: #f8fafc;
  min-width: 64px;
}
.stat-pill--green { border-color: #15803d; background: #f0fdf4; }
.stat-pill--amber { border-color: #d97706; background: #fffbeb; }
.stat-num { font-size: 18px; font-weight: 800; color: #0f172a; }
.stat-lbl { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: .06em; margin-top: 1px; }
.stat-pill--green .stat-num { color: #15803d; }
.stat-pill--amber .stat-num { color: #d97706; }

/* ── Main layout ──────────────────────────────────────────────────────── */
.vocab-layout { display: flex; gap: 20px; align-items: flex-start; }
.vocab-layout--study {
  flex-direction: row;
  align-items: stretch;
  gap: 0;
}
.vocab-layout--study .vocab-sidebar {
  min-width: 180px;
  max-width: 50%;
}
.vocab-layout--study .vocab-main {
  min-width: 260px;
}
.vocab-layout--resizing {
  cursor: col-resize;
  user-select: none;
}
.split-handle {
  flex-shrink: 0;
  width: 10px;
  margin: 0 4px;
  cursor: col-resize;
  border-radius: 6px;
  background: transparent;
  transition: background 0.15s;
  position: relative;
}
.split-handle::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 3px;
  height: 48px;
  border-radius: 3px;
  background: #e2e8f0;
  transition: background 0.15s, height 0.15s;
}
.split-handle:hover::after,
.vocab-layout--resizing .split-handle::after {
  background: #15803d;
  height: 64px;
}
.vocab-layout--study .topic-list {
  max-height: min(520px, calc(100vh - 300px));
  overflow-y: auto;
}
@media (max-width: 768px) {
  .vocab-layout--study {
    flex-direction: column;
    gap: 16px;
  }
  .vocab-layout--study .split-handle {
    display: none;
  }
  .vocab-layout--study .vocab-sidebar,
  .vocab-layout--study .vocab-main {
    flex: none !important;
    width: 100% !important;
    max-width: none !important;
  }
}

/* ── Sidebar ──────────────────────────────────────────────────────────── */
.vocab-sidebar {
  width: 240px; flex-shrink: 0;
  background: #fff; border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid #f1f5f9;
}
.sidebar-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #64748b; }
.sidebar-add-btn {
  width: 28px; height: 28px; border-radius: 8px;
  border: 1.5px solid #15803d; background: #f0fdf4; color: #15803d;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  transition: all .15s;
}
.sidebar-add-btn:hover { background: #15803d; color: #fff; }
.sidebar-loading, .sidebar-empty { padding: 16px; font-size: 13px; color: #94a3b8; text-align: center; line-height: 1.6; }
.sidebar-error { color: #e11d48; display: flex; flex-direction: column; align-items: center; }
.link-btn { background: none; border: none; color: #15803d; cursor: pointer; font-weight: 600; }

.topic-list { padding: 8px; display: flex; flex-direction: column; gap: 2px; }
.topic-item {
  display: flex; align-items: center; gap: 4px;
  padding: 10px 10px; border-radius: 10px; cursor: pointer;
  transition: all .15s; border: 1.5px solid transparent;
}
.topic-item:hover { background: #f8fafc; }
.topic-item.active { background: #f0fdf4; border-color: #15803d; }
.topic-item__body { flex: 1; min-width: 0; }
.topic-item__name { font-size: 13px; font-weight: 600; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
.topic-item.active .topic-item__name { color: #15803d; }
.topic-item__count { font-size: 10px; color: #94a3b8; margin-top: 1px; display: block; }
.topic-item__menu { flex-shrink: 0; }
.menu-btn {
  width: 24px; height: 24px; border-radius: 6px;
  background: none; border: none; color: #94a3b8; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity .15s;
}
.topic-item:hover .menu-btn { opacity: 1; }
.menu-btn:hover { background: #f1f5f9; color: #475569; }

/* ── Main panel ─────────────────────────────────────────────────────── */
.vocab-main {
  flex: 1; min-width: 0;
  background: #fff; border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.vocab-main--study {
  min-height: 420px;
}
.main-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid #f1f5f9; gap: 12px;
}
.main-title { font-size: 15px; font-weight: 800; color: #0f172a; }
.main-sub   { font-size: 12px; color: #94a3b8; margin-top: 2px; }

.main-header-actions {
  display: flex; align-items: center; gap: 8px; flex-shrink: 0;
}

.word-search-wrap {
  position: relative; display: flex; align-items: center;
}
.word-search-icon {
  position: absolute; left: 8px; color: #94a3b8; pointer-events: none;
}
.word-search-input {
  padding: 7px 28px 7px 26px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px; font-size: 12px;
  color: #0f172a; background: #f8fafc;
  outline: none; width: 160px;
  transition: border-color .15s, width .2s;
}
.word-search-input:focus {
  border-color: #15803d; width: 200px;
}
.word-search-clear {
  position: absolute; right: 6px;
  background: none; border: none; cursor: pointer;
  color: #94a3b8; display: flex; align-items: center;
  padding: 2px;
}
.word-search-clear:hover { color: #0f172a; }

.view-tabs {
  display: inline-flex; border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden;
}
.view-tab {
  padding: 6px 12px; font-size: 12px; font-weight: 600; border: none; background: #fff;
  color: #64748b; cursor: pointer;
}
.view-tab.active { background: #15803d; color: #fff; }

.add-word-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; background: #15803d; color: #fff;
  border: none; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer;
  transition: background .15s;
}
.add-word-btn:hover { background: #166534; }

/* ── Word table ──────────────────────────────────────────────────────── */
.word-table { padding: 0; }
.word-table-head {
  display: flex; gap: 0; padding: 0 20px;
  border-bottom: 1px solid #f1f5f9; background: #f8fafc;
}
.th {
  padding: 10px 8px;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .06em; color: #94a3b8;
}
.word-row {
  display: flex; align-items: center; gap: 0; padding: 0 20px;
  border-bottom: 1px solid #f8fafc; transition: background .1s;
}
.word-row:hover { background: #f8fafc; }
.td { padding: 12px 8px; font-size: 13px; color: #374151; }

.word-cell { display: flex; align-items: center; gap: 6px; }
.word-text { font-weight: 700; color: #0f172a; }
.tts-btn {
  padding: 3px; background: none; border: none; cursor: pointer;
  color: #94a3b8; border-radius: 4px; transition: all .1s;
}
.tts-btn:hover { color: #15803d; background: #f0fdf4; }
.word-phonetic { font-size: 11px; color: #94a3b8; font-style: italic; margin-top: 1px; }
.word-type-pill {
  display: inline-block;
  margin-top: 3px; padding: 1px 8px;
  background: #dcfce7; color: #15803d;
  border-radius: 6px; font-size: 10px; font-weight: 600; text-transform: uppercase;
}
.meaning-vi { color: #15803d; font-weight: 600; }
.example-text { color: #64748b; font-size: 12px; font-style: italic; }

.srs-cell { display: flex; flex-direction: column; gap: 2px; font-size: 11px; }
.srs-due { color: #b45309; font-weight: 700; }
.srs-ok { color: #64748b; }
.srs-meta { color: #94a3b8; font-size: 10px; }

.mastery-select {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 4px 8px; font-size: 11px; font-weight: 600;
  background: #f8fafc; cursor: pointer; outline: none;
  max-width: 100%;
}
.mastery--new      { border-color: #e2e8f0; color: #94a3b8; }
.mastery--learning { border-color: #fbbf24; color: #d97706; background: #fffbeb; }
.mastery--mastered { border-color: #15803d; color: #15803d; background: #f0fdf4; }

.row-actions { display: flex; gap: 4px; }
.row-action-btn {
  width: 28px; height: 28px; border-radius: 6px;
  background: none; border: 1px solid #e2e8f0; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: #94a3b8; transition: all .15s;
}
.row-action-btn:hover { border-color: #15803d; color: #15803d; background: #f0fdf4; }
.row-action-btn--del:hover { border-color: #e11d48; color: #e11d48; background: #fff1f2; }

/* ── Empty state ─────────────────────────────────────────────────────── */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; padding: 60px 20px; text-align: center;
}
.empty-icon { color: #cbd5e1; }
.empty-title { font-size: 14px; font-weight: 600; color: #94a3b8; }

/* ── Modals ───────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center; padding: 16px;
}
.modal-sm {
  background: #fff; border-radius: 20px; width: 100%; max-width: 360px;
  box-shadow: 0 24px 80px rgba(0,0,0,.18); overflow: hidden;
}
.modal-lg {
  background: #fff; border-radius: 20px; width: 100%; max-width: 560px;
  box-shadow: 0 24px 80px rgba(0,0,0,.18); overflow: hidden;
}
.modal-sm-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid #f1f5f9;
  font-size: 14px; font-weight: 700; color: #0f172a;
}
.modal-sm-header button { background: none; border: none; cursor: pointer; color: #94a3b8; padding: 4px; border-radius: 6px; }
.modal-sm-header button:hover { background: #f1f5f9; }
.modal-sm-body { padding: 16px 18px; }
.topic-input {
  width: 100%; border: 1.5px solid #e2e8f0; border-radius: 10px;
  padding: 10px 14px; font-size: 14px; outline: none; font-family: inherit;
}
.topic-input:focus { border-color: #15803d; }

.modal-lg-body { padding: 16px 18px; }
.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.col-span-2 { grid-column: span 2; }
.field label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: #94a3b8; }
.field input, .field textarea {
  border: 1.5px solid #e2e8f0; border-radius: 10px;
  padding: 8px 12px; font-size: 13px; outline: none; font-family: inherit; resize: vertical;
}
.field input:focus, .field textarea:focus { border-color: #15803d; }

.modal-sm-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 18px; border-top: 1px solid #f1f5f9;
}
.btn-cancel { padding: 8px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; color: #475569; font-size: 13px; cursor: pointer; }
.btn-green  { padding: 8px 20px; background: #15803d; color: #fff; border: none; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; }
.btn-green:disabled { opacity: .4; cursor: not-allowed; }

/* ── Topic context menu ────────────────────────────────────────────── */
.topic-ctx-menu {
  position: fixed; z-index: 10100;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 4px; box-shadow: 0 8px 24px rgba(0,0,0,.15);
  min-width: 140px;
}
.topic-ctx-menu button {
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 8px 14px; text-align: left;
  background: none; border: none; border-radius: 6px;
  font-size: 13px; color: #374151; cursor: pointer;
}
.topic-ctx-menu button:hover { background: #f1f5f9; }
.topic-ctx-menu button.danger { color: #e11d48; }
.topic-ctx-menu button.danger:hover { background: #fff1f2; }

/* ── Source badge (Reading / Listening provenance) ─────────────────── */
.source-badge {
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; padding: 2px 6px; border-radius: 4px;
  line-height: 1.4;
}
.source-badge--reading   { background: #e0f2fe; color: #0369a1; }
.source-badge--listening { background: #fef3c7; color: #92400e; }

/* ── Transitions ────────────────────────────────────────────────────── */
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity .2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

.popup-fade-enter-active, .popup-fade-leave-active { transition: opacity .15s, transform .15s; }
.popup-fade-enter-from, .popup-fade-leave-to { opacity: 0; transform: scale(.95); }
</style>

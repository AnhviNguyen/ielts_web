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

<template>
  <div class="admin-page mx-auto max-w-7xl space-y-5" :style="pageStyle">
    <AdminPageHeader module="listening" title="Listening Test Builder" subtitle="Nhập builder — JSON tự sinh khi bạn sửa nội dung.">
      <template #actions>
        <div class="flex gap-2">
          <button class="ct-btn btn-sm" :class="activeTab === 'builder' ? 'ct-btn-accent' : ''" @click="activeTab = 'builder'">Builder</button>
          <button class="ct-btn btn-sm" :class="activeTab === 'raw' ? 'ct-btn-accent' : ''" @click="activeTab = 'raw'">JSON</button>
        </div>
      </template>
    </AdminPageHeader>

    <AdminCrudBar
      module="listening"
      :can-archive="!!selectedId"
      :is-archived="isArchived"
      :saving="saving"
      :can-save="!blockingErrors.length"
      @create="newBuilder"
      @save="saveBuilder"
      @archive="archiveBuilder"
      @refresh="loadList"
    />

    <div class="rounded-lg border border-[var(--border)] bg-white p-3">
      <div class="grid gap-3 md:grid-cols-[1fr_120px]">
        <input v-model="filters.q" class="ct-input" placeholder="Search Listening tests" @keyup.enter="loadList" />
        <button class="ct-btn" @click="loadList">Filter</button>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-[360px_1fr]">
      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <h2 class="text-sm font-bold text-[var(--ink)]">Listening tests</h2>
          <button class="ct-btn btn-sm" @click="newBuilder">New</button>
        </div>
        <div class="max-h-[760px] overflow-y-auto">
          <button
            v-for="item in items"
            :key="item.id"
            class="block w-full border-b border-[var(--border)] px-4 py-3 text-left hover:bg-[var(--bg)]"
            :class="selectedId === item.id ? 'admin-list-active' : ''"
            @click="selectItem(item.id)"
          >
            <div class="line-clamp-2 text-sm font-semibold text-[var(--ink)]">{{ item.title || item.id }}<span v-if="item.status === 'archived' || item.status === 0" class="ml-1.5 inline-block rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">Đã ẩn</span></div>
            <div class="mt-1 text-xs text-[var(--ink3)]">#{{ item.id }} - {{ item.book_code || 'Listening' }} - {{ item.quizzes?.full?.question_count || 0 }} questions</div>
          </button>
          <div v-if="!items.length" class="p-6 text-center text-sm text-[var(--ink3)]">No Listening tests found.</div>
        </div>
      </section>

      <section class="min-w-0 space-y-4">
        <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>
        <div v-if="savedMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ savedMessage }}</div>

        <template v-if="activeTab === 'builder'">
          <div class="rounded-lg border border-[var(--border)] bg-white p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-bold text-[var(--ink)]">Metadata</h2>
                <p class="mt-1 text-xs text-[var(--ink3)]">Saved as skill_id 2 so it appears on the public Listening page.</p>
              </div>
              <div class="flex flex-wrap items-center gap-2 text-xs">
                <span class="rounded-md bg-[var(--bg)] px-2 py-1 font-semibold text-[var(--ink2)]">{{ totalQuestions }} question rows</span>
                <span class="rounded-md bg-rose-50 px-2 py-1 font-semibold text-rose-700">{{ blockingErrors.length }} errors</span>
                <span class="rounded-md bg-amber-50 px-2 py-1 font-semibold text-amber-700">{{ softWarnings.length }} warnings</span>
              </div>
            </div>

            <div class="mt-4 grid gap-3 md:grid-cols-2">
              <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="builder.title" class="ct-input mt-1 w-full" /></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Book code<input v-model="builder.book_code" class="ct-input mt-1 w-full" /></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Status
                <select v-model="builder.status" class="ct-input mt-1 w-full">
                  <option value="published">published</option>
                  <option value="draft">draft</option>
                  <option value="archived">archived</option>
                </select>
              </label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Time (minutes)<input v-model.number="builder.time" type="number" min="1" class="ct-input mt-1 w-full" /></label>
            </div>

            <div class="mt-4 grid gap-3 md:grid-cols-[160px_1fr]">
              <div class="aspect-video overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg)]">
                <img v-if="thumbnailPreview" :src="thumbnailPreview" class="h-full w-full object-cover" alt="" />
                <div v-else class="flex h-full items-center justify-center text-xs text-[var(--ink3)]">No image</div>
              </div>
              <div class="space-y-2">
                <div class="text-xs font-semibold text-[var(--ink3)]">Thumbnail image</div>
                <input type="file" accept="image/png,image/jpeg,image/webp" class="block w-full text-sm" @change="uploadThumbnail" />
                <div class="rounded-md bg-[var(--bg)] px-2 py-1 font-mono text-xs text-[var(--ink3)]">{{ builder.thumbnail || 'No thumbnail id' }}</div>
                <button class="ct-btn btn-sm" :disabled="!builder.thumbnail" @click="builder.thumbnail = ''">Clear image</button>
              </div>
            </div>
          </div>

          <div class="rounded-lg border border-[var(--border)] bg-white">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
              <div class="flex gap-2">
                <button
                  v-for="(_, idx) in builder.parts"
                  :key="idx"
                  class="ct-btn btn-sm"
                  :class="selectedPartIndex === idx ? 'ct-btn-accent' : ''"
                  @click="selectPart(idx)"
                >
                  Section {{ idx + 1 }}
                </button>
              </div>
              <button class="ct-btn btn-sm" @click="addSet">Add question set</button>
            </div>

            <div class="grid gap-0 xl:grid-cols-[1fr_340px]">
              <div class="space-y-4 p-4">
                <div class="grid gap-3 md:grid-cols-[1fr_110px_1fr]">
                  <label class="text-xs font-semibold text-[var(--ink3)]">Section title<input v-model="currentPart.title" class="ct-input mt-1 w-full" /></label>
                  <label class="text-xs font-semibold text-[var(--ink3)]">Section time (minutes)<input v-model.number="currentPart.time" type="number" min="1" class="ct-input mt-1 w-full" /></label>
                  <div class="space-y-1">
                    <div class="text-xs font-semibold text-[var(--ink3)]">Audio file</div>
                    <input type="file" accept="audio/mpeg,audio/mp4,audio/ogg,audio/wav,.mp3,.m4a,.ogg,.wav" class="block w-full text-sm" @change="uploadAudio" />
                    <div class="rounded-md bg-[var(--bg)] px-2 py-1 font-mono text-xs text-[var(--ink3)]">{{ currentPart.file_id || 'No audio id' }}</div>
                  </div>
                </div>
                <audio v-if="audioPreviewUrl" :src="audioPreviewUrl" controls class="w-full" />
                <div class="grid gap-3 md:grid-cols-2">
                  <label class="text-xs font-semibold text-[var(--ink3)]">Listen from seconds<input v-model.number="currentPart.listen_from" type="number" min="0" class="ct-input mt-1 w-full" /></label>
                  <label class="text-xs font-semibold text-[var(--ink3)]">Listen to seconds<input v-model.number="currentPart.listen_to" type="number" min="0" class="ct-input mt-1 w-full" /></label>
                </div>
                <label class="block text-xs font-semibold text-[var(--ink3)]">Transcript text
                  <textarea v-model="currentPart.transcript_text" class="ct-input mt-1 min-h-[260px] w-full" placeholder="One transcript paragraph per line. Optional: Speaker: text"></textarea>
                </label>
              </div>
              <aside class="border-t border-[var(--border)] p-4 xl:border-l xl:border-t-0">
                <h3 class="text-sm font-bold text-[var(--ink)]">Question sets</h3>
                <div class="mt-3 space-y-2">
                  <button
                    v-for="(set, idx) in currentPart.question_sets"
                    :key="idx"
                    class="block w-full rounded-lg border border-[var(--border)] px-3 py-2 text-left text-sm hover:bg-[var(--bg)]"
                    :class="selectedSetIndex === idx ? 'border-emerald-300 bg-emerald-50' : 'bg-white'"
                    @click="selectedSetIndex = idx"
                  >
                    <div class="font-semibold text-[var(--ink)]">{{ set.title || `Set ${idx + 1}` }}</div>
                    <div class="mt-0.5 text-xs text-[var(--ink3)]">{{ templateLabel(set.template) }} - {{ set.questions.length }} questions</div>
                  </button>
                  <div v-if="!currentPart.question_sets.length" class="rounded-lg bg-[var(--bg)] p-4 text-sm text-[var(--ink3)]">No question set yet.</div>
                </div>
              </aside>
            </div>
          </div>

          <div v-if="currentSet" class="rounded-lg border border-[var(--border)] bg-white p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-bold text-[var(--ink)]">Set editor</h2>
                <p class="mt-1 text-xs text-[var(--ink3)]">{{ currentTemplateHelp }}</p>
              </div>
              <div class="flex gap-2">
                <button class="ct-btn btn-sm" @click="addQuestion">Add question</button>
                <button class="ct-btn btn-sm" @click="removeSet">Remove set</button>
              </div>
            </div>

            <div class="mt-4 grid gap-3 md:grid-cols-2">
              <label class="text-xs font-semibold text-[var(--ink3)]">Set title<input v-model="currentSet.title" class="ct-input mt-1 w-full" /></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Template
                <select v-model="currentSet.template" class="ct-input mt-1 w-full" @change="applyTemplate(currentSet)">
                  <option v-for="tpl in setTemplates" :key="tpl.value" :value="tpl.value">{{ tpl.label }}</option>
                </select>
              </label>
            </div>
            <label class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Instruction / description<textarea v-model="currentSet.description" class="ct-input mt-1 min-h-[70px] w-full"></textarea></label>
            <label v-if="isGapSet" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Inline gap prompt, use {{ gapToken }} once per question<textarea v-model="currentSet.content" class="ct-input mt-1 min-h-[120px] w-full"></textarea></label>
            <label v-if="needsSetOptions" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Options: A|Option text, A|B|C, or A-G<textarea v-model="currentSet.options_text" class="ct-input mt-1 min-h-[100px] w-full font-mono text-xs" @input="syncSetOptions(currentSet)"></textarea></label>

            <div class="mt-4 overflow-x-auto">
              <table class="w-full min-w-[980px] text-left text-xs">
                <thead class="bg-[var(--bg)] text-[var(--ink3)]">
                  <tr>
                    <th class="px-3 py-2">#</th>
                    <th class="px-3 py-2">{{ questionTextLabel }}</th>
                    <th v-if="isSingleSet" class="px-3 py-2">Question options</th>
                    <th class="px-3 py-2">Answer</th>
                    <th class="px-3 py-2">Listen from</th>
                    <th class="px-3 py-2">Locate</th>
                    <th class="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(q, idx) in currentSet.questions" :key="idx" class="border-t border-[var(--border)] align-top">
                    <td class="px-3 py-2 font-semibold">{{ questionOrder(selectedPartIndex, selectedSetIndex, idx) }}</td>
                    <td class="px-3 py-2"><textarea v-model="q.text" class="ct-input min-h-[58px] w-full"></textarea></td>
                    <td v-if="isSingleSet" class="px-3 py-2"><textarea v-model="q.options_text" class="ct-input min-h-[58px] w-full font-mono text-xs" @input="syncQuestionOptions(q)"></textarea></td>
                    <td class="px-3 py-2">
                      <select v-if="answerChoicesForQuestion(q).length" v-model="q.correct_answer" class="ct-input w-full">
                        <option value="">Select answer</option>
                        <option v-for="choice in answerChoicesForQuestion(q)" :key="choice" :value="choice">{{ choice }}</option>
                      </select>
                      <input v-else v-model="q.correct_answer" class="ct-input w-full" :placeholder="answerPlaceholder" />
                    </td>
                    <td class="px-3 py-2"><input v-model.number="q.listen_from" type="number" min="0" class="ct-input w-24" /></td>
                    <td class="px-3 py-2"><input v-model.number="q.locate_paragraph" type="number" min="1" class="ct-input w-20" /></td>
                    <td class="px-3 py-2 text-right"><button class="ct-btn btn-sm" @click="removeQuestion(idx)">Remove</button></td>
                  </tr>
                  <tr v-if="!currentSet.questions.length">
                    <td :colspan="isSingleSet ? 7 : 6" class="px-3 py-8 text-center text-sm text-[var(--ink3)]">No questions in this set.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="rounded-lg border border-[var(--border)] bg-white p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-bold text-[var(--ink)]">Validation</h2>
                <p class="mt-1 text-xs text-[var(--ink3)]">Errors block saving. Fewer than 40 rows is allowed when several IELTS items are grouped into one question.</p>
              </div>
              <div class="flex gap-2">
                <button class="ct-btn ct-btn-accent" :disabled="saving || blockingErrors.length" @click="saveBuilder">{{ saving ? 'Saving...' : 'Save Listening test' }}</button>
              </div>
            </div>
            <ul v-if="blockingErrors.length" class="mt-3 space-y-1 text-sm text-rose-700"><li v-for="warning in blockingErrors" :key="warning">- {{ warning }}</li></ul>
            <ul v-if="softWarnings.length" class="mt-3 space-y-1 text-sm text-amber-700"><li v-for="warning in softWarnings" :key="warning">- {{ warning }}</li></ul>
            <div v-if="!blockingErrors.length && !softWarnings.length" class="mt-3 text-sm text-emerald-700">Builder payload looks complete.</div>
          </div>
        </template>

        <div v-else class="space-y-3">
          <div class="flex justify-end gap-2">
            <button class="ct-btn btn-sm" @click="runSync">Cập nhật JSON</button>
            <button class="ct-btn btn-sm" @click="refreshRawPreview">Tải từ server</button>
          </div>
          <AdminJsonPanel v-model="rawText" module="listening" tall :live="jsonLive" :syncing="jsonSyncing" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'
import AdminCrudBar from '@/components/admin/AdminCrudBar.vue'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminJsonPanel from '@/components/admin/AdminJsonPanel.vue'
import { moduleStyle } from '@/components/admin/adminModules.js'
import { useAutoJsonSync } from '@/composables/useAutoJsonSync.js'
import { imageUrl } from '@/utils/mediaUrl.js'
import { buildAudioSrc } from '@/utils/audio.js'

const pageStyle = moduleStyle('listening')

const TEMPLATE_INLINE_GAP = 'INLINE_GAP_TEXT'
const TEMPLATE_TF_NG = 'TF_NG'
const TEMPLATE_YN_NG = 'YN_NG'
const TEMPLATE_SINGLE = 'SINGLE_CHOICE'
const TEMPLATE_MULTI = 'MULTIPLE_CHOICE_MANY'
const TEMPLATE_MATCHING = 'MATCHING_SELECT'
const TEMPLATE_TEXT = 'TEXT_COMPLETION'

const setTemplates = [
  { value: TEMPLATE_INLINE_GAP, label: 'Inline Gap Text', help: 'Prompt contains {{gap}} placeholders. Each placeholder maps to one text answer.' },
  { value: TEMPLATE_TF_NG, label: 'TF/NG', help: 'Questions use TRUE, FALSE, or NOT GIVEN.' },
  { value: TEMPLATE_YN_NG, label: 'YN/NG', help: 'Questions use YES, NO, or NOT GIVEN.' },
  { value: TEMPLATE_SINGLE, label: 'Single Choice', help: 'Each question can have A/B/C options.' },
  { value: TEMPLATE_MULTI, label: 'Multiple Choice Many', help: 'Shared options bank. Answers use comma-separated letters such as A,C.' },
  { value: TEMPLATE_MATCHING, label: 'Matching / Select', help: 'Shared option bank and each question selects one letter.' },
  { value: TEMPLATE_TEXT, label: 'Short / Completion Text', help: 'Plain text answer. Use | for accepted alternatives.' },
]

const activeTab = ref('builder')
const items = ref([])
const selectedId = ref(null)
const selectedPartIndex = ref(0)
const selectedSetIndex = ref(0)
const rawText = ref('')
const lastRawJson = ref(null)
const error = ref('')
const savedMessage = ref('')
const saving = ref(false)
const filters = reactive({ q: '' })
const builder = reactive(emptyBuilder())

const { jsonLive, jsonSyncing, pause, resume, runSync } = useAutoJsonSync(builder, () => {
  rawText.value = JSON.stringify({ builder: payload() }, null, 2)
})
const gapToken = '{{gap}}'
const fixedAnswers = {
  [TEMPLATE_TF_NG]: ['TRUE', 'FALSE', 'NOT GIVEN'],
  [TEMPLATE_YN_NG]: ['YES', 'NO', 'NOT GIVEN'],
}

const currentPart = computed(() => builder.parts[selectedPartIndex.value] || builder.parts[0])
const currentSet = computed(() => currentPart.value?.question_sets?.[selectedSetIndex.value] || null)
const thumbnailPreview = computed(() => imageUrl(builder.thumbnail))
const audioPreviewUrl = computed(() => buildAudioSrc(currentPart.value?.file_id))
const totalQuestions = computed(() => builder.parts.reduce((sum, part) => sum + part.question_sets.reduce((setSum, set) => setSum + set.questions.length, 0), 0))
const isGapSet = computed(() => currentSet.value?.template === TEMPLATE_INLINE_GAP)
const isSingleSet = computed(() => currentSet.value?.template === TEMPLATE_SINGLE)
const isMultiSet = computed(() => currentSet.value?.template === TEMPLATE_MULTI)
const isMatchingSet = computed(() => currentSet.value?.template === TEMPLATE_MATCHING)
const needsSetOptions = computed(() => [TEMPLATE_SINGLE, TEMPLATE_MULTI, TEMPLATE_MATCHING].includes(currentSet.value?.template))
const currentTemplateHelp = computed(() => setTemplates.find((tpl) => tpl.value === currentSet.value?.template)?.help || '')
const questionTextLabel = computed(() => isGapSet.value ? 'Gap note / label' : 'Question text')
const answerPlaceholder = computed(() => isMultiSet.value ? 'A,C' : 'answer|accepted alternative')
const blockingErrors = computed(() => validateBuilder().errors)
const softWarnings = computed(() => validateBuilder().warnings)

const isArchived = computed(() => {
  if (!selectedId.value) return false
  const item = items.value.find(x => x.id === selectedId.value)
  return item && (item.status === 'archived' || item.status === 0)
})

function emptyBuilder() {
  return {
    id: null,
    title: 'New Listening Mock Test',
    book_code: 'Admin',
    status: 'published',
    time: 40,
    thumbnail: '',
    parts: [1, 2, 3, 4].map((n) => ({ title: `Listening Part ${n}`, time: n === 4 ? 10 : 8, file_id: '', transcript_text: '', listen_from: null, listen_to: null, question_sets: [] })),
  }
}

function normalizeBuilder(payload) {
  const next = emptyBuilder()
  Object.assign(next, payload || {})
  next.parts = [0, 1, 2, 3].map((idx) => {
    const part = next.parts?.[idx] || {}
    return {
      title: part.title || `Listening Part ${idx + 1}`,
      time: Number(part.time || 8),
      file_id: part.file_id || '',
      transcript_text: part.transcript_text || '',
      listen_from: part.listen_from ?? null,
      listen_to: part.listen_to ?? null,
      question_sets: (part.question_sets || []).map(normalizeSet),
    }
  })
  return next
}

function normalizeSet(set) {
  const template = normalizeTemplate(set)
  return {
    title: set.title || '',
    template,
    question_type: questionTypeForTemplate(template, set.question_type),
    description: set.description || '',
    content: set.content || '',
    options: set.options || [],
    options_text: set.options_text ?? optionsText(set.options || []),
    questions: (set.questions || []).map((question) => ({
      text: question.text || '',
      correct_answer: question.correct_answer || (question.correct_answers || []).join(template === TEMPLATE_MULTI ? ',' : '|'),
      correct_answers: question.correct_answers || [],
      options: question.options || [],
      options_text: question.options_text ?? optionsText(question.options || []),
      explain: question.explain || '',
      locate_paragraph: question.locate_paragraph || null,
      listen_from: question.listen_from ?? null,
    })),
    max_selections: set.max_selections || null,
  }
}

function resetBuilder(next = emptyBuilder()) {
  Object.assign(builder, JSON.parse(JSON.stringify(next)))
  selectedPartIndex.value = 0
  selectedSetIndex.value = 0
}

function normalizeTemplate(set = {}) {
  const raw = String(set.template || set.question_type || '').toUpperCase()
  if (['INLINE_GAP_TEXT', 'GAP_FILLING'].includes(raw)) return TEMPLATE_INLINE_GAP
  if (['TF_NG', 'TRUE_FALSE'].includes(raw)) return TEMPLATE_TF_NG
  if (['YN_NG', 'YES_NO'].includes(raw)) return TEMPLATE_YN_NG
  if (['SINGLE_CHOICE', 'SINGLE_SELECTION', 'MULTIPLE_CHOICE_ONE'].includes(raw)) return TEMPLATE_SINGLE
  if (raw === TEMPLATE_MULTI) return TEMPLATE_MULTI
  if (raw.startsWith('MATCHING') || raw === 'TABLE_SELECTION') return TEMPLATE_MATCHING
  return TEMPLATE_TEXT
}

function questionTypeForTemplate(template, currentType = '') {
  if (template === TEMPLATE_INLINE_GAP) return 'GAP_FILLING'
  if (template === TEMPLATE_TF_NG) return 'TRUE_FALSE'
  if (template === TEMPLATE_YN_NG) return 'YES_NO'
  if (template === TEMPLATE_SINGLE) return 'SINGLE_CHOICE'
  if (template === TEMPLATE_MULTI) return 'MULTIPLE_CHOICE_MANY'
  if (template === TEMPLATE_MATCHING) return ['MATCHING', 'MATCHING_FEATURES', 'MATCHING_INFO', 'MATCHING_HEADINGS', 'MATCHING_ENDINGS', 'TABLE_SELECTION'].includes(currentType) ? currentType : 'MATCHING'
  return ['SHORT_ANSWER', 'SENTENCE_COMPLETION', 'SUMMARY_COMPLETION', 'NOTE_COMPLETION'].includes(currentType) ? currentType : 'SHORT_ANSWER'
}

function applyTemplate(set) {
  set.question_type = questionTypeForTemplate(set.template, set.question_type)
  if (set.template === TEMPLATE_INLINE_GAP) set.options = []
  if (set.template !== TEMPLATE_MULTI) set.max_selections = null
}

async function loadList() {
  const data = await adminService.listMockTests({ skill_id: 2, q: filters.q || undefined })
  items.value = data.items || []
}

async function selectItem(id) {
  pause()
  error.value = ''
  savedMessage.value = ''
  selectedId.value = id
  activeTab.value = 'builder'
  try {
    const data = await adminService.getListeningMockTestBuilder(id)
    resetBuilder(normalizeBuilder(data.builder))
    lastRawJson.value = data.raw_json
    rawText.value = JSON.stringify(data.raw_json, null, 2)
  } catch (err) {
    error.value = detailMessage(err, 'Cannot load this Listening test.')
  } finally {
    resume()
  }
}

async function uploadThumbnail(event) {
  const file = event.target.files?.[0]
  if (!file) return
  error.value = ''
  savedMessage.value = ''
  try {
    const result = await adminService.uploadAdminImage(file)
    builder.thumbnail = result.id
    savedMessage.value = 'Thumbnail uploaded.'
  } catch (err) {
    error.value = detailMessage(err, 'Cannot upload thumbnail.')
  } finally {
    event.target.value = ''
  }
}

async function uploadAudio(event) {
  const file = event.target.files?.[0]
  if (!file) return
  error.value = ''
  savedMessage.value = ''
  try {
    const result = await adminService.uploadAdminAudio(file)
    currentPart.value.file_id = result.id
    savedMessage.value = `Audio uploaded for Section ${selectedPartIndex.value + 1}.`
  } catch (err) {
    error.value = detailMessage(err, 'Cannot upload audio.')
  } finally {
    event.target.value = ''
  }
}

function newBuilder() {
  selectedId.value = null
  error.value = ''
  savedMessage.value = ''
  activeTab.value = 'builder'
  lastRawJson.value = null
  resetBuilder()
}

function selectPart(idx) {
  selectedPartIndex.value = idx
  selectedSetIndex.value = 0
}

function addSet() {
  currentPart.value.question_sets.push(normalizeSet({ title: `Questions ${totalQuestions.value + 1}-`, template: TEMPLATE_INLINE_GAP, question_type: 'GAP_FILLING' }))
  selectedSetIndex.value = currentPart.value.question_sets.length - 1
}

function removeSet() {
  currentPart.value.question_sets.splice(selectedSetIndex.value, 1)
  selectedSetIndex.value = Math.max(0, selectedSetIndex.value - 1)
}

function addQuestion() {
  if (!currentSet.value) addSet()
  currentSet.value.questions.push({ text: '', correct_answer: '', correct_answers: [], options: [], options_text: '', explain: '', locate_paragraph: null, listen_from: currentPart.value.listen_from ?? null })
}

function removeQuestion(idx) {
  currentSet.value.questions.splice(idx, 1)
}

function questionOrder(partIdx, setIdx, qIdx) {
  let order = 0
  for (let p = 0; p < builder.parts.length; p += 1) {
    for (let s = 0; s < builder.parts[p].question_sets.length; s += 1) {
      for (let q = 0; q < builder.parts[p].question_sets[s].questions.length; q += 1) {
        order += 1
        if (p === partIdx && s === setIdx && q === qIdx) return order
      }
    }
  }
  return order + 1
}

function parseOptions(value) {
  const raw = String(value || '').trim()
  if (/^[A-Z]\s*-\s*[A-Z]$/i.test(raw)) {
    const [start, end] = raw.toUpperCase().split(/\s*-\s*/)
    return Array.from({ length: end.charCodeAt(0) - start.charCodeAt(0) + 1 }, (_, idx) => ({ option: String.fromCharCode(start.charCodeAt(0) + idx), text: '' }))
  }
  const lines = raw.split('\n').map(line => line.trim()).filter(Boolean)
  if (lines.length === 1 && /^[A-Z0-9]+(?:\s*\|\s*[A-Z0-9]+)+$/i.test(lines[0])) return lines[0].split('|').map(part => ({ option: part.trim().toUpperCase(), text: '' }))
  return lines.map((line, idx) => {
    const parts = line.includes('|') ? line.split('|') : [String.fromCharCode(65 + idx), line]
    return { option: parts[0].trim().toUpperCase(), text: parts.slice(1).join('|').trim() }
  })
}

function optionsText(options) {
  return (options || []).map((option) => `${option.option}|${option.text || ''}`).join('\n')
}

function syncSetOptions(set) {
  set.options = parseOptions(set.options_text)
}

function syncQuestionOptions(question) {
  question.options = parseOptions(question.options_text)
}

function optionKeys(options) {
  return (options || []).map((option) => String(option.option || '').trim().toUpperCase()).filter(Boolean)
}

function answerChoicesForQuestion(question) {
  if (!currentSet.value) return []
  if (fixedAnswers[currentSet.value.template]) return fixedAnswers[currentSet.value.template]
  if (currentSet.value.template === TEMPLATE_MATCHING) return optionKeys(currentSet.value.options)
  if (currentSet.value.template === TEMPLATE_SINGLE) return optionKeys(question.options?.length ? question.options : currentSet.value.options)
  return []
}

function templateLabel(value) {
  return setTemplates.find((tpl) => tpl.value === value)?.label || value || 'Template'
}

function gapCount(content) {
  const raw = String(content || '')
  const explicit = (raw.match(/\{\{\s*gap\s*\}\}/gi) || []).length
  if (explicit) return explicit
  return (raw.match(/gap-placeholder/gi) || []).length
}

function answersForTemplate(template, value) {
  if ([TEMPLATE_INLINE_GAP, TEMPLATE_TEXT].includes(template)) return String(value || '').split('|').map(part => part.trim()).filter(Boolean)
  return String(value || '').split(/[|,]/).map(part => part.trim()).filter(Boolean)
}

function validateBuilder() {
  const errors = []
  const warnings = []
  if (!builder.title.trim()) errors.push('Title is required.')
  if (builder.parts.length !== 4) errors.push('Listening test must have 4 sections.')
  builder.parts.forEach((part, partIdx) => {
    if (!part.question_sets.length) errors.push(`Section ${partIdx + 1} has no question set.`)
    if (!part.file_id) warnings.push(`Section ${partIdx + 1} has no audio file id.`)
    part.question_sets.forEach((set, setIdx) => {
      if (!set.questions.length) errors.push(`Section ${partIdx + 1} set ${setIdx + 1} has no questions.`)
      if (set.template === TEMPLATE_INLINE_GAP && gapCount(set.content) > 0 && gapCount(set.content) !== set.questions.length) warnings.push(`Section ${partIdx + 1} set ${setIdx + 1} gap count differs from question rows. This is OK for grouped questions.`)
      if ([TEMPLATE_MULTI, TEMPLATE_MATCHING].includes(set.template) && !set.options.length) errors.push(`Section ${partIdx + 1} set ${setIdx + 1} needs options.`)
      if (set.template === TEMPLATE_SINGLE && !set.options.length && !set.questions.some((q) => q.options.length)) errors.push(`Section ${partIdx + 1} set ${setIdx + 1} needs shared or per-question options.`)
      const setKeys = optionKeys(set.options)
      set.questions.forEach((question, qIdx) => {
        const order = questionOrder(partIdx, setIdx, qIdx)
        const answers = answersForTemplate(set.template, question.correct_answer)
        if (!answers.length) errors.push(`Question ${order} needs an answer.`)
        if (set.template !== TEMPLATE_INLINE_GAP && !String(question.text || '').trim()) errors.push(`Question ${order} needs question text.`)
        const upperAnswers = answers.map((answer) => answer.toUpperCase())
        if (fixedAnswers[set.template] && upperAnswers.some((answer) => !fixedAnswers[set.template].includes(answer))) errors.push(`Question ${order} answer must be one of ${fixedAnswers[set.template].join(', ')}.`)
        if (set.template === TEMPLATE_SINGLE) {
          const keys = optionKeys(question.options.length ? question.options : set.options)
          if (!keys.length || answers.length !== 1 || !keys.includes(upperAnswers[0])) errors.push(`Question ${order} answer must match its options.`)
        }
        if (set.template === TEMPLATE_MULTI && upperAnswers.some((answer) => !setKeys.includes(answer))) errors.push(`Question ${order} answers must match the option bank.`)
        if (set.template === TEMPLATE_MATCHING && (answers.length !== 1 || !setKeys.includes(upperAnswers[0]))) errors.push(`Question ${order} answer must match the option bank.`)
      })
    })
  })
  if (totalQuestions.value !== 40) warnings.push('Listening normally has 40 IELTS items; saving with fewer question rows is allowed for grouped questions.')
  return { errors, warnings }
}

function payload() {
  const cloned = JSON.parse(JSON.stringify(builder))
  cloned.parts.forEach((part) => {
    part.question_sets.forEach((set) => {
      set.template = normalizeTemplate(set)
      set.question_type = questionTypeForTemplate(set.template, set.question_type)
      set.options = [TEMPLATE_INLINE_GAP, TEMPLATE_TF_NG, TEMPLATE_YN_NG].includes(set.template) ? [] : parseOptions(set.options_text ?? optionsText(set.options || []))
      delete set.options_text
      set.questions.forEach((question) => {
        question.options = set.template === TEMPLATE_SINGLE ? parseOptions(question.options_text ?? optionsText(question.options || [])) : []
        delete question.options_text
        question.correct_answer = String(question.correct_answer || '').trim()
        question.correct_answers = answersForTemplate(set.template, question.correct_answer)
      })
    })
  })
  return cloned
}

function previewPayload() {
  rawText.value = JSON.stringify({ builder: payload() }, null, 2)
}

function refreshRawPreview() {
  if (lastRawJson.value) rawText.value = JSON.stringify(lastRawJson.value, null, 2)
  else previewPayload()
}

async function saveBuilder() {
  error.value = ''
  savedMessage.value = ''
  if (blockingErrors.value.length) {
    error.value = 'Please fix validation errors before saving.'
    return
  }
  saving.value = true
  try {
    const body = payload()
    const result = selectedId.value
      ? await adminService.updateListeningMockTestBuilder(selectedId.value, body)
      : await adminService.createListeningMockTestBuilder(body)
    selectedId.value = result.mock_test_id
    resetBuilder(normalizeBuilder(result.builder))
    lastRawJson.value = result.raw_json
    rawText.value = JSON.stringify(result.raw_json, null, 2)
    savedMessage.value = `Saved Listening test #${result.mock_test_id}. Backups: ${result.backup_paths?.length || 0}`
    await loadList()
  } catch (err) {
    error.value = detailMessage(err, 'Cannot save Listening builder.')
  } finally {
    saving.value = false
  }
}

async function archiveBuilder() {
  if (!selectedId.value) return
  if (isArchived.value) {
    if (!window.confirm('Hiện lại đề này? Đề sẽ hiển thị lại cho người dùng.')) return
    saving.value = true
    try {
      await adminService.restoreMockTest(selectedId.value)
      savedMessage.value = 'Đã hiện lại đề Listening.'
      await loadList()
      await selectItem(selectedId.value)
    } catch (err) {
      error.value = detailMessage(err, 'Không hiện lại được.')
    } finally {
      saving.value = false
    }
  } else {
    if (!window.confirm('Ẩn đề này? Đề sẽ không hiển thị cho người dùng.')) return
    saving.value = true
    try {
      await adminService.archiveMockTest(selectedId.value)
      selectedId.value = null
      savedMessage.value = 'Đã ẩn đề Listening.'
      await loadList()
      newBuilder()
    } catch (err) {
      error.value = detailMessage(err, 'Không ẩn được.')
    } finally {
      saving.value = false
    }
  }
}

function detailMessage(err, fallback) {
  const detail = err?.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg || JSON.stringify(item)).join('; ')
  return detail || err?.message || fallback
}

onMounted(async () => {
  await loadList()
  if (items.value.length) await selectItem(items.value[0].id)
  else newBuilder()
})
</script>

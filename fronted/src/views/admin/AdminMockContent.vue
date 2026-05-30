<template>
  <div class="mx-auto max-w-7xl space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Reading Mock Test Builder</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Tao de Reading bang form, server tu sinh JSON cho trang lam bai.</p>
      </div>
      <div class="flex gap-2">
        <button class="ct-btn" :class="activeTab === 'builder' ? 'ct-btn-accent' : ''" @click="activeTab = 'builder'">Builder</button>
        <button class="ct-btn" :class="activeTab === 'raw' ? 'ct-btn-accent' : ''" @click="activeTab = 'raw'">Raw preview</button>
      </div>
    </div>

    <div class="rounded-lg border border-[var(--border)] bg-white p-3">
      <div class="grid gap-3 md:grid-cols-[1fr_120px]">
        <input v-model="filters.q" class="ct-input" placeholder="Search Reading mock tests" @keyup.enter="loadList" />
        <button class="ct-btn" @click="loadList">Filter</button>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-[360px_1fr]">
      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <h2 class="text-sm font-bold text-[var(--ink)]">Reading tests</h2>
          <button class="ct-btn btn-sm" @click="newBuilder">New</button>
        </div>
        <div class="max-h-[760px] overflow-y-auto">
          <button
            v-for="item in items"
            :key="item.id"
            class="block w-full border-b border-[var(--border)] px-4 py-3 text-left hover:bg-[var(--bg)]"
            :class="selectedId === item.id ? 'bg-emerald-50' : ''"
            @click="selectItem(item.id)"
          >
            <div class="line-clamp-2 text-sm font-semibold text-[var(--ink)]">{{ item.title || item.id }}</div>
            <div class="mt-1 text-xs text-[var(--ink3)]">
              #{{ item.id }} · {{ item.book_code || 'Reading' }} · {{ item.quizzes?.full?.question_count || 0 }} questions
            </div>
          </button>
          <div v-if="!items.length" class="p-6 text-center text-sm text-[var(--ink3)]">No Reading mock tests found.</div>
        </div>
      </section>

      <section class="space-y-4">
        <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>
        <div v-if="savedMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ savedMessage }}</div>

        <template v-if="activeTab === 'builder'">
          <div class="rounded-lg border border-[var(--border)] bg-white p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-bold text-[var(--ink)]">Metadata</h2>
                <p class="mt-1 text-xs text-[var(--ink3)]">Thumbnail luu thanh image id trong backend/data/assets/images.</p>
              </div>
              <div class="flex flex-wrap items-center gap-2 text-xs">
                <span class="rounded-md bg-[var(--bg)] px-2 py-1 font-semibold text-[var(--ink2)]">{{ totalQuestions }}/40 questions</span>
                <span class="rounded-md bg-[var(--bg)] px-2 py-1 font-semibold text-[var(--ink2)]">{{ warningCount }} warnings</span>
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
                <img v-if="builder.thumbnail" :src="thumbnailPreview" class="h-full w-full object-cover" alt="" />
                <div v-else class="flex h-full items-center justify-center text-xs text-[var(--ink3)]">No image</div>
              </div>
              <div class="space-y-2">
                <label class="text-xs font-semibold text-[var(--ink3)]">Thumbnail image id<input v-model="builder.thumbnail" class="ct-input mt-1 w-full" /></label>
                <input type="file" accept="image/png,image/jpeg,image/webp" class="block w-full text-sm" @change="uploadThumbnail" />
              </div>
            </div>
          </div>

          <div class="rounded-lg border border-[var(--border)] bg-white">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
              <div class="flex gap-2">
                <button
                  v-for="(_, idx) in builder.passages"
                  :key="idx"
                  class="ct-btn btn-sm"
                  :class="selectedPassageIndex === idx ? 'ct-btn-accent' : ''"
                  @click="selectPassage(idx)"
                >
                  Passage {{ idx + 1 }}
                </button>
              </div>
              <button class="ct-btn btn-sm" @click="addSet">Add question set</button>
            </div>

            <div class="grid gap-0 lg:grid-cols-[1fr_360px]">
              <div class="space-y-4 p-4">
                <label class="text-xs font-semibold text-[var(--ink3)]">Passage title<input v-model="currentPassage.title" class="ct-input mt-1 w-full" /></label>
                <label class="text-xs font-semibold text-[var(--ink3)]">Passage text
                  <textarea v-model="currentPassage.passage_text" class="ct-input mt-1 min-h-[320px] w-full" placeholder="One paragraph per line"></textarea>
                </label>
              </div>

              <aside class="border-t border-[var(--border)] p-4 lg:border-l lg:border-t-0">
                <h3 class="text-sm font-bold text-[var(--ink)]">Question sets</h3>
                <div class="mt-3 space-y-2">
                  <button
                    v-for="(set, idx) in currentPassage.question_sets"
                    :key="idx"
                    class="block w-full rounded-lg border border-[var(--border)] px-3 py-2 text-left text-sm hover:bg-[var(--bg)]"
                    :class="selectedSetIndex === idx ? 'border-emerald-300 bg-emerald-50' : 'bg-white'"
                    @click="selectedSetIndex = idx"
                  >
                    <div class="font-semibold text-[var(--ink)]">{{ set.title || `Set ${idx + 1}` }}</div>
                    <div class="mt-0.5 text-xs text-[var(--ink3)]">{{ set.question_type }} · {{ set.questions.length }} questions</div>
                  </button>
                  <div v-if="!currentPassage.question_sets.length" class="rounded-lg bg-[var(--bg)] p-4 text-sm text-[var(--ink3)]">No question set yet.</div>
                </div>
              </aside>
            </div>
          </div>

          <div v-if="currentSet" class="rounded-lg border border-[var(--border)] bg-white p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <h2 class="text-sm font-bold text-[var(--ink)]">Set editor</h2>
              <div class="flex gap-2">
                <button class="ct-btn btn-sm" @click="addQuestion">Add question</button>
                <button class="ct-btn btn-sm" @click="removeSet">Remove set</button>
              </div>
            </div>

            <div class="mt-4 grid gap-3 md:grid-cols-2">
              <label class="text-xs font-semibold text-[var(--ink3)]">Set title<input v-model="currentSet.title" class="ct-input mt-1 w-full" /></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Question type
                <select v-model="currentSet.question_type" class="ct-input mt-1 w-full">
                  <option v-for="type in questionTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
              </label>
            </div>

            <label class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Instruction / description
              <textarea v-model="currentSet.description" class="ct-input mt-1 min-h-[70px] w-full"></textarea>
            </label>

            <label v-if="isGapSet" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Gap prompt, use <span v-pre>{{gap}}</span> for each blank
              <textarea v-model="currentSet.content" class="ct-input mt-1 min-h-[120px] w-full"></textarea>
            </label>

            <label v-if="needsOptions" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Options, one per line: A|Option text
              <textarea :value="optionsText(currentSet.options)" class="ct-input mt-1 min-h-[130px] w-full font-mono text-xs" @input="currentSet.options = parseOptions($event.target.value)"></textarea>
            </label>

            <label v-if="isMultiSet" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Max selections
              <input v-model.number="currentSet.max_selections" type="number" min="1" class="ct-input mt-1 w-40" />
            </label>

            <div class="mt-4 overflow-x-auto">
              <table class="w-full min-w-[760px] text-left text-xs">
                <thead class="bg-[var(--bg)] text-[var(--ink3)]">
                  <tr>
                    <th class="px-3 py-2">#</th>
                    <th class="px-3 py-2">Question text</th>
                    <th class="px-3 py-2">Answer</th>
                    <th class="px-3 py-2">Locate</th>
                    <th class="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(q, idx) in currentSet.questions" :key="idx" class="border-t border-[var(--border)] align-top">
                    <td class="px-3 py-2 font-semibold">{{ questionOrder(selectedPassageIndex, selectedSetIndex, idx) }}</td>
                    <td class="px-3 py-2"><textarea v-model="q.text" class="ct-input min-h-[58px] w-full"></textarea></td>
                    <td class="px-3 py-2">
                      <input v-model="q.correct_answer" class="ct-input w-full" :placeholder="answerPlaceholder" />
                      <div class="mt-1 text-[11px] text-[var(--ink3)]">{{ answerHint }}</div>
                    </td>
                    <td class="px-3 py-2"><input v-model.number="q.locate_paragraph" type="number" min="1" class="ct-input w-20" /></td>
                    <td class="px-3 py-2 text-right"><button class="ct-btn btn-sm" @click="removeQuestion(idx)">Remove</button></td>
                  </tr>
                  <tr v-if="!currentSet.questions.length">
                    <td colspan="5" class="px-3 py-8 text-center text-sm text-[var(--ink3)]">No questions in this set.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="rounded-lg border border-[var(--border)] bg-white p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-bold text-[var(--ink)]">Validation</h2>
                <p class="mt-1 text-xs text-[var(--ink3)]">Backend se reject neu thieu passage, dap an, options, hoac khong du 40 cau.</p>
              </div>
              <div class="flex gap-2">
                <button class="ct-btn" @click="previewPayload">Preview JSON</button>
                <button class="ct-btn ct-btn-accent" :disabled="saving" @click="saveBuilder">{{ saving ? 'Saving...' : 'Save Reading test' }}</button>
              </div>
            </div>
            <ul v-if="warnings.length" class="mt-3 space-y-1 text-sm text-amber-700">
              <li v-for="warning in warnings" :key="warning">- {{ warning }}</li>
            </ul>
            <div v-else class="mt-3 text-sm text-emerald-700">Builder payload looks complete.</div>
          </div>
        </template>

        <div v-else class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-bold text-[var(--ink)]">Raw JSON advanced</h2>
              <p class="mt-1 text-xs text-[var(--ink3)]">Dung de debug. Luong chinh van la Builder.</p>
            </div>
            <div class="flex gap-2">
              <button class="ct-btn" @click="refreshRawPreview">Refresh preview</button>
              <button class="ct-btn" @click="saveRawMock">Save raw mock JSON</button>
            </div>
          </div>
          <textarea v-model="rawText" class="ct-input min-h-[620px] w-full font-mono text-xs"></textarea>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'

const questionTypes = [
  { value: 'GAP_FILLING', label: 'Gap/text completion' },
  { value: 'SHORT_ANSWER', label: 'Short answer' },
  { value: 'SENTENCE_COMPLETION', label: 'Sentence completion' },
  { value: 'SUMMARY_COMPLETION', label: 'Summary completion' },
  { value: 'NOTE_COMPLETION', label: 'Note completion' },
  { value: 'MAP_DIAGRAM_LABEL', label: 'Map/diagram label' },
  { value: 'TRUE_FALSE', label: 'True / False / Not Given' },
  { value: 'YES_NO', label: 'Yes / No / Not Given' },
  { value: 'SINGLE_CHOICE', label: 'Single choice' },
  { value: 'MULTIPLE_CHOICE_MANY', label: 'Multiple choice many' },
  { value: 'MATCHING', label: 'Matching' },
  { value: 'MATCHING_HEADING', label: 'Matching heading' },
  { value: 'MATCHING_HEADINGS', label: 'Matching headings' },
  { value: 'MATCHING_INFO', label: 'Matching information' },
  { value: 'MATCHING_FEATURES', label: 'Matching features' },
  { value: 'MATCHING_ENDINGS', label: 'Matching endings' },
  { value: 'TABLE_SELECTION', label: 'Table selection' },
]

const optionTypes = new Set([
  'SINGLE_CHOICE',
  'MULTIPLE_CHOICE_MANY',
  'MATCHING',
  'MATCHING_HEADING',
  'MATCHING_HEADINGS',
  'MATCHING_INFO',
  'MATCHING_FEATURES',
  'MATCHING_ENDINGS',
  'TABLE_SELECTION',
])

const activeTab = ref('builder')
const items = ref([])
const selectedId = ref(null)
const selectedPassageIndex = ref(0)
const selectedSetIndex = ref(0)
const rawText = ref('')
const lastRawJson = ref(null)
const error = ref('')
const savedMessage = ref('')
const saving = ref(false)
const filters = reactive({ q: '' })

const builder = reactive(emptyBuilder())

const currentPassage = computed(() => builder.passages[selectedPassageIndex.value] || builder.passages[0])
const currentSet = computed(() => currentPassage.value?.question_sets?.[selectedSetIndex.value] || null)
const thumbnailPreview = computed(() => builder.thumbnail ? `/api/images/${builder.thumbnail}` : '')
const totalQuestions = computed(() =>
  builder.passages.reduce((sum, passage) => sum + passage.question_sets.reduce((setSum, set) => setSum + set.questions.length, 0), 0)
)
const isGapSet = computed(() => currentSet.value?.question_type === 'GAP_FILLING')
const isMultiSet = computed(() => currentSet.value?.question_type === 'MULTIPLE_CHOICE_MANY')
const needsOptions = computed(() => optionTypes.has(currentSet.value?.question_type))
const answerPlaceholder = computed(() => isMultiSet.value ? 'A,C' : 'Answer or alternative 1|alternative 2')
const answerHint = computed(() => isMultiSet.value ? 'Use comma for multiple answers.' : 'Use | for accepted alternatives.')

const warnings = computed(() => {
  const rows = []
  if (!builder.title.trim()) rows.push('Title is required.')
  if (builder.passages.length !== 3) rows.push('Reading test must have 3 passages.')
  builder.passages.forEach((passage, passageIdx) => {
    if (!passage.passage_text.trim()) rows.push(`Passage ${passageIdx + 1} has no text.`)
    if (!passage.question_sets.length) rows.push(`Passage ${passageIdx + 1} has no question set.`)
    passage.question_sets.forEach((set, setIdx) => {
      if (!set.questions.length) rows.push(`Passage ${passageIdx + 1} set ${setIdx + 1} has no questions.`)
      if (optionTypes.has(set.question_type) && !set.options.length) rows.push(`Passage ${passageIdx + 1} set ${setIdx + 1} needs options.`)
      if (set.question_type === 'GAP_FILLING') {
        const gaps = (set.content.match(/\{\{\s*gap\s*\}\}/gi) || []).length
        if (gaps && gaps !== set.questions.length) rows.push(`Passage ${passageIdx + 1} set ${setIdx + 1} gap count does not match questions.`)
      }
      set.questions.forEach((question, qIdx) => {
        if (!String(question.correct_answer || '').trim()) rows.push(`Question ${questionOrder(passageIdx, setIdx, qIdx)} needs an answer.`)
      })
    })
  })
  if (totalQuestions.value !== 40) rows.push('Reading mock test should contain exactly 40 questions.')
  return rows
})
const warningCount = computed(() => warnings.value.length)

function emptyBuilder() {
  return {
    id: null,
    title: 'New Reading Mock Test',
    book_code: 'Admin',
    status: 'published',
    time: 60,
    thumbnail: '',
    passages: [1, 2, 3].map((n) => ({ title: `Passage ${n}`, passage_text: '', question_sets: [] })),
  }
}

function resetBuilder(next = emptyBuilder()) {
  Object.assign(builder, JSON.parse(JSON.stringify(next)))
  selectedPassageIndex.value = 0
  selectedSetIndex.value = 0
  previewPayload()
}

function normalizeBuilder(payload) {
  const next = emptyBuilder()
  Object.assign(next, payload || {})
  next.passages = [0, 1, 2].map((idx) => {
    const passage = next.passages?.[idx] || {}
    return {
      title: passage.title || `Passage ${idx + 1}`,
      passage_text: passage.passage_text || '',
      question_sets: (passage.question_sets || []).map(normalizeSet),
    }
  })
  return next
}

function normalizeSet(set) {
  return {
    title: set.title || '',
    question_type: set.question_type || 'SHORT_ANSWER',
    description: set.description || '',
    content: set.content || '',
    options: set.options || [],
    questions: (set.questions || []).map((question) => ({
      text: question.text || '',
      correct_answer: question.correct_answer || (question.correct_answers || []).join('|'),
      correct_answers: question.correct_answers || [],
      options: question.options || [],
      explain: question.explain || '',
      locate_paragraph: question.locate_paragraph || null,
    })),
    max_selections: set.max_selections || null,
  }
}

async function loadList() {
  const data = await adminService.listMockTests({ skill_id: 1, q: filters.q || undefined })
  items.value = data.items || []
}

async function selectItem(id) {
  error.value = ''
  savedMessage.value = ''
  selectedId.value = id
  activeTab.value = 'builder'
  try {
    const data = await adminService.getReadingMockTestBuilder(id)
    resetBuilder(normalizeBuilder(data.builder))
    lastRawJson.value = data.raw_json
    rawText.value = JSON.stringify(data.raw_json, null, 2)
  } catch (err) {
    lastRawJson.value = null
    rawText.value = ''
    error.value = detailMessage(err, 'Cannot load the real quiz JSON for this Reading test.')
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

function selectPassage(idx) {
  selectedPassageIndex.value = idx
  selectedSetIndex.value = 0
}

function addSet() {
  currentPassage.value.question_sets.push(normalizeSet({ title: `Set ${currentPassage.value.question_sets.length + 1}`, question_type: 'SHORT_ANSWER' }))
  selectedSetIndex.value = currentPassage.value.question_sets.length - 1
}

function removeSet() {
  if (!currentSet.value) return
  currentPassage.value.question_sets.splice(selectedSetIndex.value, 1)
  selectedSetIndex.value = Math.max(0, selectedSetIndex.value - 1)
}

function addQuestion() {
  if (!currentSet.value) addSet()
  currentSet.value.questions.push({
    text: '',
    correct_answer: '',
    correct_answers: [],
    options: [],
    explain: '',
    locate_paragraph: null,
  })
}

function removeQuestion(idx) {
  currentSet.value?.questions.splice(idx, 1)
}

function questionOrder(passageIdx, setIdx, qIdx) {
  let order = 0
  for (let p = 0; p < builder.passages.length; p += 1) {
    const passage = builder.passages[p]
    for (let s = 0; s < passage.question_sets.length; s += 1) {
      const set = passage.question_sets[s]
      for (let q = 0; q < set.questions.length; q += 1) {
        order += 1
        if (p === passageIdx && s === setIdx && q === qIdx) return order
      }
    }
  }
  return order + 1
}

function parseOptions(value) {
  return String(value || '')
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
    .map((line, idx) => {
      const parts = line.includes('|') ? line.split('|') : [String.fromCharCode(65 + idx), line]
      return { option: parts[0].trim(), text: parts.slice(1).join('|').trim() }
    })
}

function optionsText(options) {
  return (options || []).map((option) => `${option.option}|${option.text || ''}`).join('\n')
}

async function uploadThumbnail(event) {
  const file = event.target.files?.[0]
  if (!file) return
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

function payload() {
  const cloned = JSON.parse(JSON.stringify(builder))
  cloned.passages.forEach((passage) => {
    passage.question_sets.forEach((set) => {
      set.questions.forEach((question) => {
        question.correct_answers = splitAnswers(question.correct_answer)
      })
    })
  })
  return cloned
}

function splitAnswers(value) {
  return String(value || '').split(/[|,]/).map(part => part.trim()).filter(Boolean)
}

function previewPayload() {
  rawText.value = JSON.stringify({ builder: payload() }, null, 2)
}

function refreshRawPreview() {
  if (lastRawJson.value) {
    rawText.value = JSON.stringify(lastRawJson.value, null, 2)
    return
  }
  previewPayload()
}

async function saveBuilder() {
  error.value = ''
  savedMessage.value = ''
  saving.value = true
  try {
    const body = payload()
    const result = selectedId.value
      ? await adminService.updateReadingMockTestBuilder(selectedId.value, body)
      : await adminService.createReadingMockTestBuilder(body)
    selectedId.value = result.mock_test_id
    resetBuilder(normalizeBuilder(result.builder))
    lastRawJson.value = result.raw_json
    rawText.value = JSON.stringify(result.raw_json, null, 2)
    savedMessage.value = `Saved Reading mock test #${result.mock_test_id}. Backups: ${result.backup_paths?.length || 0}`
    await loadList()
  } catch (err) {
    error.value = detailMessage(err, 'Cannot save Reading builder.')
  } finally {
    saving.value = false
  }
}

async function saveRawMock() {
  error.value = ''
  savedMessage.value = ''
  try {
    const raw = JSON.parse(rawText.value)
    const id = selectedId.value || raw.data?.id || raw.id
    const result = id ? await adminService.updateMockTest(id, raw) : await adminService.createMockTest(raw)
    selectedId.value = result.item.id
    lastRawJson.value = result.raw_json
    rawText.value = JSON.stringify(result.raw_json, null, 2)
    savedMessage.value = `Saved raw mock JSON. Backup: ${result.backup_path || 'none'}`
    await loadList()
  } catch (err) {
    error.value = detailMessage(err, 'Cannot save raw JSON.')
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

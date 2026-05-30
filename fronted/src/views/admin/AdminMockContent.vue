<template>
  <div class="mx-auto max-w-7xl space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Reading Mock Test Builder</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Create Reading tests with structured templates; JSON is generated for the public quiz runner.</p>
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
              #{{ item.id }} - {{ item.book_code || 'Reading' }} - {{ item.quizzes?.full?.question_count || 0 }} questions
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
                <p class="mt-1 text-xs text-[var(--ink3)]">Thumbnail is stored as an image id in backend/data/assets/images.</p>
              </div>
              <div class="flex flex-wrap items-center gap-2 text-xs">
                <span class="rounded-md bg-[var(--bg)] px-2 py-1 font-semibold text-[var(--ink2)]">{{ totalQuestions }}/40 questions</span>
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
              <button class="ct-btn btn-sm" @click="addSet">Add template set</button>
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
                    <div class="mt-0.5 text-xs text-[var(--ink3)]">{{ templateLabel(set.template) }} - {{ set.questions.length }} questions</div>
                  </button>
                  <div v-if="!currentPassage.question_sets.length" class="rounded-lg bg-[var(--bg)] p-4 text-sm text-[var(--ink3)]">No question set yet.</div>
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

            <div v-if="isMatchingSet || isTextSet" class="mt-3 grid gap-3 md:grid-cols-2">
              <label v-if="isMatchingSet" class="text-xs font-semibold text-[var(--ink3)]">Matching renderer type
                <select v-model="currentSet.question_type" class="ct-input mt-1 w-full">
                  <option v-for="type in matchingQuestionTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
              </label>
              <label v-if="isTextSet" class="text-xs font-semibold text-[var(--ink3)]">Text answer type
                <select v-model="currentSet.question_type" class="ct-input mt-1 w-full">
                  <option v-for="type in textQuestionTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
              </label>
            </div>

            <label class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Instruction / description
              <textarea v-model="currentSet.description" class="ct-input mt-1 min-h-[70px] w-full"></textarea>
            </label>

            <label v-if="isGapSet" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Inline gap prompt, use <span v-pre>{{gap}}</span> once per question
              <textarea v-model="currentSet.content" class="ct-input mt-1 min-h-[120px] w-full"></textarea>
            </label>

            <label v-if="needsSetOptions" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">{{ optionLabel }}
              <textarea v-model="currentSet.options_text" class="ct-input mt-1 min-h-[120px] w-full font-mono text-xs" @input="syncSetOptions(currentSet)"></textarea>
            </label>

            <label v-if="isMultiSet" class="mt-3 block text-xs font-semibold text-[var(--ink3)]">Max selections
              <input v-model.number="currentSet.max_selections" type="number" min="1" class="ct-input mt-1 w-40" />
            </label>

            <div class="mt-4 overflow-x-auto">
              <table class="w-full min-w-[900px] text-left text-xs">
                <thead class="bg-[var(--bg)] text-[var(--ink3)]">
                  <tr>
                    <th class="px-3 py-2">#</th>
                    <th class="px-3 py-2">{{ questionTextLabel }}</th>
                    <th v-if="isSingleSet" class="px-3 py-2">Question options</th>
                    <th class="px-3 py-2">Answer</th>
                    <th class="px-3 py-2">Locate</th>
                    <th class="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(q, idx) in currentSet.questions" :key="idx" class="border-t border-[var(--border)] align-top">
                    <td class="px-3 py-2 font-semibold">{{ questionOrder(selectedPassageIndex, selectedSetIndex, idx) }}</td>
                    <td class="px-3 py-2"><textarea v-model="q.text" class="ct-input min-h-[58px] w-full"></textarea></td>
                    <td v-if="isSingleSet" class="px-3 py-2">
                      <textarea v-model="q.options_text" class="ct-input min-h-[58px] w-full font-mono text-xs" placeholder="A|Option text" @input="syncQuestionOptions(q)"></textarea>
                    </td>
                    <td class="px-3 py-2">
                      <select v-if="answerChoicesForQuestion(q).length" v-model="q.correct_answer" class="ct-input w-full">
                        <option value="">Select answer</option>
                        <option v-for="choice in answerChoicesForQuestion(q)" :key="choice" :value="choice">{{ choice }}</option>
                      </select>
                      <input v-else v-model="q.correct_answer" class="ct-input w-full" :placeholder="answerPlaceholder" />
                      <div class="mt-1 text-[11px] text-[var(--ink3)]">{{ answerHint }}</div>
                    </td>
                    <td class="px-3 py-2"><input v-model.number="q.locate_paragraph" type="number" min="1" class="ct-input w-20" /></td>
                    <td class="px-3 py-2 text-right"><button class="ct-btn btn-sm" @click="removeQuestion(idx)">Remove</button></td>
                  </tr>
                  <tr v-if="!currentSet.questions.length">
                    <td :colspan="isSingleSet ? 6 : 5" class="px-3 py-8 text-center text-sm text-[var(--ink3)]">No questions in this set.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="rounded-lg border border-[var(--border)] bg-white p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-bold text-[var(--ink)]">Validation</h2>
                <p class="mt-1 text-xs text-[var(--ink3)]">Errors block saving. The 40-question total is a warning so old data can still be edited.</p>
              </div>
              <div class="flex gap-2">
                <button class="ct-btn" @click="previewPayload">Preview JSON</button>
                <button class="ct-btn ct-btn-accent" :disabled="saving || blockingErrors.length" @click="saveBuilder">{{ saving ? 'Saving...' : 'Save Reading test' }}</button>
              </div>
            </div>
            <ul v-if="blockingErrors.length" class="mt-3 space-y-1 text-sm text-rose-700">
              <li v-for="warning in blockingErrors" :key="warning">- {{ warning }}</li>
            </ul>
            <ul v-if="softWarnings.length" class="mt-3 space-y-1 text-sm text-amber-700">
              <li v-for="warning in softWarnings" :key="warning">- {{ warning }}</li>
            </ul>
            <div v-if="!blockingErrors.length && !softWarnings.length" class="mt-3 text-sm text-emerald-700">Builder payload looks complete.</div>
          </div>
        </template>

        <div v-else class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-bold text-[var(--ink)]">Raw JSON advanced</h2>
              <p class="mt-1 text-xs text-[var(--ink3)]">For inspection and debug. The main flow is the Builder.</p>
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
  { value: TEMPLATE_SINGLE, label: 'Single Choice', help: 'Each question can have its own A/B/C options, or use shared options from the set.' },
  { value: TEMPLATE_MULTI, label: 'Multiple Choice Many', help: 'Shared options bank. Answers use comma-separated letters such as A,C.' },
  { value: TEMPLATE_MATCHING, label: 'Matching / Select', help: 'Shared option bank is added to the description, and each question selects one letter.' },
  { value: TEMPLATE_TEXT, label: 'Short / Completion Text', help: 'Plain text answer. Use | for accepted alternatives.' },
]

const textQuestionTypes = [
  { value: 'SHORT_ANSWER', label: 'Short answer' },
  { value: 'SENTENCE_COMPLETION', label: 'Sentence completion' },
  { value: 'SUMMARY_COMPLETION', label: 'Summary completion' },
  { value: 'NOTE_COMPLETION', label: 'Note completion' },
  { value: 'MAP_DIAGRAM_LABEL', label: 'Map/diagram label' },
]

const matchingQuestionTypes = [
  { value: 'MATCHING', label: 'Matching' },
  { value: 'MATCHING_HEADING', label: 'Matching heading' },
  { value: 'MATCHING_HEADINGS', label: 'Matching headings' },
  { value: 'MATCHING_INFO', label: 'Matching information' },
  { value: 'MATCHING_FEATURES', label: 'Matching features' },
  { value: 'MATCHING_ENDINGS', label: 'Matching endings' },
  { value: 'TABLE_SELECTION', label: 'Table selection' },
]

const fixedAnswers = {
  [TEMPLATE_TF_NG]: ['TRUE', 'FALSE', 'NOT GIVEN'],
  [TEMPLATE_YN_NG]: ['YES', 'NO', 'NOT GIVEN'],
}

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
const isGapSet = computed(() => currentSet.value?.template === TEMPLATE_INLINE_GAP)
const isSingleSet = computed(() => currentSet.value?.template === TEMPLATE_SINGLE)
const isMultiSet = computed(() => currentSet.value?.template === TEMPLATE_MULTI)
const isMatchingSet = computed(() => currentSet.value?.template === TEMPLATE_MATCHING)
const isTextSet = computed(() => currentSet.value?.template === TEMPLATE_TEXT)
const needsSetOptions = computed(() => [TEMPLATE_SINGLE, TEMPLATE_MULTI, TEMPLATE_MATCHING].includes(currentSet.value?.template))
const optionLabel = computed(() => isSingleSet.value ? 'Shared options: A|Option text, or A|B|C' : 'Option bank: A|Option text, A|B|C, or A-G')
const currentTemplateHelp = computed(() => setTemplates.find((tpl) => tpl.value === currentSet.value?.template)?.help || '')
const questionTextLabel = computed(() => isGapSet.value ? 'Gap note / label' : 'Question text')
const answerPlaceholder = computed(() => {
  if (isMultiSet.value) return 'A,C'
  if (isGapSet.value || isTextSet.value) return 'answer|accepted alternative'
  return 'Answer option'
})
const answerHint = computed(() => {
  if (isMultiSet.value) return 'Use comma for multiple letters.'
  if (isGapSet.value || isTextSet.value) return 'Use | for accepted alternatives.'
  if (isSingleSet.value) return 'Answer must match one option letter.'
  if (isMatchingSet.value) return 'Answer must match the option bank.'
  return 'Select one allowed answer.'
})

const blockingErrors = computed(() => validateBuilder().errors)
const softWarnings = computed(() => validateBuilder().warnings)

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
    })),
    max_selections: set.max_selections || null,
  }
}

function normalizeTemplate(set = {}) {
  const raw = String(set.template || set.question_type || '').toUpperCase()
  if ([TEMPLATE_INLINE_GAP, 'GAP_FILLING'].includes(raw)) return TEMPLATE_INLINE_GAP
  if ([TEMPLATE_TF_NG, 'TRUE_FALSE'].includes(raw)) return TEMPLATE_TF_NG
  if ([TEMPLATE_YN_NG, 'YES_NO'].includes(raw)) return TEMPLATE_YN_NG
  if ([TEMPLATE_SINGLE, 'SINGLE_SELECTION', 'MULTIPLE_CHOICE_ONE'].includes(raw)) return TEMPLATE_SINGLE
  if (raw === TEMPLATE_MULTI) return TEMPLATE_MULTI
  if (matchingQuestionTypes.some((type) => type.value === raw) || raw === TEMPLATE_MATCHING) return TEMPLATE_MATCHING
  return TEMPLATE_TEXT
}

function questionTypeForTemplate(template, currentType = '') {
  if (template === TEMPLATE_INLINE_GAP) return 'GAP_FILLING'
  if (template === TEMPLATE_TF_NG) return 'TRUE_FALSE'
  if (template === TEMPLATE_YN_NG) return 'YES_NO'
  if (template === TEMPLATE_SINGLE) return 'SINGLE_CHOICE'
  if (template === TEMPLATE_MULTI) return 'MULTIPLE_CHOICE_MANY'
  if (template === TEMPLATE_MATCHING) return matchingQuestionTypes.some((type) => type.value === currentType) ? currentType : 'MATCHING'
  if (template === TEMPLATE_TEXT) return textQuestionTypes.some((type) => type.value === currentType) ? currentType : 'SHORT_ANSWER'
  return currentType || 'SHORT_ANSWER'
}

function applyTemplate(set) {
  if (!set) return
  set.question_type = questionTypeForTemplate(set.template, set.question_type)
  if (set.template === TEMPLATE_INLINE_GAP) {
    set.options = []
    set.questions.forEach((question) => { question.options = [] })
  }
  if (![TEMPLATE_MULTI].includes(set.template)) set.max_selections = null
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
  currentPassage.value.question_sets.push(normalizeSet({ title: `Set ${currentPassage.value.question_sets.length + 1}`, template: TEMPLATE_INLINE_GAP, question_type: 'GAP_FILLING' }))
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
    options_text: '',
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
  const raw = String(value || '').trim()
  if (/^[A-Z]\s*-\s*[A-Z]$/i.test(raw)) {
    const [start, end] = raw.toUpperCase().split(/\s*-\s*/)
    const first = start.charCodeAt(0)
    const last = end.charCodeAt(0)
    if (first <= last) {
      return Array.from({ length: last - first + 1 }, (_, idx) => {
        const key = String.fromCharCode(first + idx)
        return { option: key, text: '' }
      })
    }
  }

  const lines = raw
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
  if (lines.every(line => /^[A-Z0-9]+(?:\s*\|\s*[A-Z0-9]+)*$/i.test(line))) {
    const compactParts = lines.flatMap(line => line.split('|').map(part => part.trim()).filter(Boolean))
    if (compactParts.length > 2 && compactParts.every(part => /^[A-Z0-9]+$/i.test(part))) {
      return compactParts.map(part => ({ option: part.toUpperCase(), text: '' }))
    }
  }

  return lines.map((line, idx) => {
    const parts = line.includes('|') ? line.split('|') : [String.fromCharCode(65 + idx), line]
    if (!line.includes('|') && /^[A-Z0-9]+$/i.test(line)) {
      return { option: line.toUpperCase(), text: '' }
    }
    return { option: parts[0].trim().toUpperCase(), text: parts.slice(1).join('|').trim() }
  })
}

function optionsText(options) {
  return (options || []).map((option) => `${option.option}|${option.text || ''}`).join('\n')
}

function syncSetOptions(set) {
  if (!set) return
  set.options = parseOptions(set.options_text)
}

function syncQuestionOptions(question) {
  if (!question) return
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
  const ids = (raw.match(/data-question-id=["']gf_/gi) || []).length
  if (ids) return ids
  return (raw.match(/gap-placeholder/gi) || []).length
}

function validateBuilder() {
  const errors = []
  const warnings = []
  if (!builder.title.trim()) errors.push('Title is required.')
  if (builder.passages.length !== 3) errors.push('Reading test must have 3 passages.')
  builder.passages.forEach((passage, passageIdx) => {
    if (!passage.passage_text.trim()) errors.push(`Passage ${passageIdx + 1} has no text.`)
    if (!passage.question_sets.length) errors.push(`Passage ${passageIdx + 1} has no question set.`)
    passage.question_sets.forEach((set, setIdx) => {
      const template = set.template
      if (!set.questions.length) errors.push(`Passage ${passageIdx + 1} set ${setIdx + 1} has no questions.`)
      if (template === TEMPLATE_INLINE_GAP && gapCount(set.content) !== set.questions.length) errors.push(`Passage ${passageIdx + 1} set ${setIdx + 1} gap count must match questions.`)
      if (template === TEMPLATE_INLINE_GAP && set.options.length) errors.push(`Passage ${passageIdx + 1} set ${setIdx + 1} inline gap cannot use options.`)
      if ([TEMPLATE_MULTI, TEMPLATE_MATCHING].includes(template) && !set.options.length) errors.push(`Passage ${passageIdx + 1} set ${setIdx + 1} needs options.`)
      if (template === TEMPLATE_SINGLE && !set.options.length && !set.questions.some((q) => q.options.length)) errors.push(`Passage ${passageIdx + 1} set ${setIdx + 1} needs shared or per-question options.`)

      const setKeys = optionKeys(set.options)
      set.questions.forEach((question, qIdx) => {
        const order = questionOrder(passageIdx, setIdx, qIdx)
        const answers = answersForTemplate(template, question.correct_answer)
        if (!answers.length) errors.push(`Question ${order} needs an answer.`)
        if (template !== TEMPLATE_INLINE_GAP && !String(question.text || '').trim()) errors.push(`Question ${order} needs question text.`)
        const upperAnswers = answers.map((answer) => answer.toUpperCase())
        if (fixedAnswers[template] && upperAnswers.some((answer) => !fixedAnswers[template].includes(answer))) errors.push(`Question ${order} answer must be one of ${fixedAnswers[template].join(', ')}.`)
        if (template === TEMPLATE_SINGLE) {
          const keys = optionKeys(question.options.length ? question.options : set.options)
          if (!keys.length) errors.push(`Question ${order} needs options.`)
          else if (answers.length !== 1 || !keys.includes(upperAnswers[0])) errors.push(`Question ${order} answer must match its options.`)
        }
        if (template === TEMPLATE_MULTI) {
          if (upperAnswers.some((answer) => !setKeys.includes(answer))) errors.push(`Question ${order} answers must match the option bank.`)
          if (set.max_selections && answers.length > Number(set.max_selections)) errors.push(`Question ${order} exceeds max selections.`)
        }
        if (template === TEMPLATE_MATCHING && (answers.length !== 1 || !setKeys.includes(upperAnswers[0]))) errors.push(`Question ${order} answer must match the option bank.`)
      })
    })
  })
  if (totalQuestions.value !== 40) warnings.push('Reading mock test should contain exactly 40 questions.')
  return { errors, warnings }
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
      set.template = normalizeTemplate(set)
      set.question_type = questionTypeForTemplate(set.template, set.question_type)
      if (set.template === TEMPLATE_INLINE_GAP) set.options = []
      else set.options = parseOptions(set.options_text ?? optionsText(set.options || []))
      delete set.options_text
      set.questions.forEach((question) => {
        if (set.template === TEMPLATE_SINGLE) question.options = parseOptions(question.options_text ?? optionsText(question.options || []))
        else question.options = []
        delete question.options_text
        question.correct_answer = String(question.correct_answer || '').trim()
        question.correct_answers = answersForTemplate(set.template, question.correct_answer)
      })
    })
  })
  return cloned
}

function answersForTemplate(template, value) {
  if ([TEMPLATE_INLINE_GAP, TEMPLATE_TEXT].includes(template)) return String(value || '').split('|').map(part => part.trim()).filter(Boolean)
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
  if (blockingErrors.value.length) {
    error.value = 'Please fix validation errors before saving.'
    return
  }
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

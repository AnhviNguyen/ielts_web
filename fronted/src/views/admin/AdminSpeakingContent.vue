<template>
  <div class="admin-page mx-auto max-w-7xl space-y-5" :style="pageStyle">
    <AdminPageHeader module="speaking" title="Speaking Test Builder" subtitle="Nhập builder — JSON tự sinh khi bạn sửa nội dung.">
      <template #actions>
        <div class="flex gap-2">
          <button class="ct-btn btn-sm" :class="activeTab === 'builder' ? 'ct-btn-accent' : ''" @click="activeTab = 'builder'">Builder</button>
          <button class="ct-btn btn-sm" :class="activeTab === 'raw' ? 'ct-btn-accent' : ''" @click="activeTab = 'raw'">JSON</button>
        </div>
      </template>
    </AdminPageHeader>

    <AdminCrudBar
      module="speaking"
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
        <input v-model="filters.q" class="ct-input" placeholder="Search Speaking tests" @keyup.enter="loadList" />
        <button class="ct-btn" @click="loadList">Filter</button>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-[360px_1fr]">
      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <h2 class="text-sm font-bold text-[var(--ink)]">Speaking tests</h2>
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
            <div class="mt-1 text-xs text-[var(--ink3)]">
              #{{ item.id }} - {{ item.book_code || 'Speaking' }} - {{ item.quizzes?.full?.question_count || 0 }} questions
            </div>
          </button>
          <div v-if="!items.length" class="p-6 text-center text-sm text-[var(--ink3)]">No Speaking tests found.</div>
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
                <p class="mt-1 text-xs text-[var(--ink3)]">Saved as a Speaking mock test so it appears on the public Speaking page.</p>
              </div>
              <div class="flex flex-wrap items-center gap-2 text-xs">
                <span class="rounded-md bg-[var(--bg)] px-2 py-1 font-semibold text-[var(--ink2)]">{{ totalQuestions }} questions</span>
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
                <label class="text-xs font-semibold text-[var(--ink3)]">Thumbnail image id<input v-model="builder.thumbnail" class="ct-input mt-1 w-full" /></label>
                <input type="file" accept="image/png,image/jpeg,image/webp" class="block w-full text-sm" @change="uploadThumbnail" />
              </div>
            </div>
          </div>

          <div class="rounded-lg border border-[var(--border)] bg-white">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
              <div class="flex gap-2">
                <button
                  v-for="(part, idx) in builder.parts"
                  :key="idx"
                  class="ct-btn btn-sm"
                  :class="selectedPartIndex === idx ? 'ct-btn-accent' : ''"
                  @click="selectedPartIndex = idx"
                >
                  Part {{ idx + 1 }}
                </button>
              </div>
              <button class="ct-btn btn-sm" @click="addQuestion">Add question</button>
            </div>

            <div class="space-y-4 p-4">
              <div class="grid gap-3 md:grid-cols-[1fr_120px]">
                <label class="text-xs font-semibold text-[var(--ink3)]">Part title<input v-model="currentPart.title" class="ct-input mt-1 w-full" /></label>
                <label class="text-xs font-semibold text-[var(--ink3)]">Part time<input v-model.number="currentPart.time" type="number" min="1" class="ct-input mt-1 w-full" /></label>
              </div>
              <label class="block text-xs font-semibold text-[var(--ink3)]">Instruction HTML
                <textarea v-model="currentPart.instruction_html" class="ct-input mt-1 min-h-[110px] w-full font-mono text-xs"></textarea>
              </label>

              <div class="overflow-x-auto">
                <table class="w-full min-w-[980px] text-left text-xs">
                  <thead class="bg-[var(--bg)] text-[var(--ink3)]">
                    <tr>
                      <th class="px-3 py-2">#</th>
                      <th class="px-3 py-2">Question title</th>
                      <th class="px-3 py-2">Cue card / description HTML</th>
                      <th class="px-3 py-2">Think</th>
                      <th class="px-3 py-2">Answer</th>
                      <th class="px-3 py-2">Audio URL</th>
                      <th class="px-3 py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(question, idx) in currentPart.questions" :key="idx" class="border-t border-[var(--border)] align-top">
                      <td class="px-3 py-2 font-semibold">{{ idx + 1 }}</td>
                      <td class="px-3 py-2"><textarea v-model="question.title" class="ct-input min-h-[70px] w-full"></textarea></td>
                      <td class="px-3 py-2"><textarea v-model="question.description" class="ct-input min-h-[90px] w-full font-mono text-xs"></textarea></td>
                      <td class="px-3 py-2"><input v-model.number="question.time_to_think" type="number" min="0" class="ct-input w-20" /></td>
                      <td class="px-3 py-2"><input v-model.number="question.time_limit" type="number" min="1" class="ct-input w-20" /></td>
                      <td class="px-3 py-2"><input v-model="question.audio_url" class="ct-input w-full" /></td>
                      <td class="px-3 py-2 text-right">
                        <div class="flex justify-end gap-1">
                          <button class="ct-btn btn-sm" :disabled="idx === 0" @click="moveQuestion(idx, -1)">Up</button>
                          <button class="ct-btn btn-sm" :disabled="idx === currentPart.questions.length - 1" @click="moveQuestion(idx, 1)">Down</button>
                          <button class="ct-btn btn-sm" @click="removeQuestion(idx)">Remove</button>
                        </div>
                      </td>
                    </tr>
                    <tr v-if="!currentPart.questions.length">
                      <td colspan="7" class="px-3 py-8 text-center text-sm text-[var(--ink3)]">No questions in this part.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="grid gap-4 xl:grid-cols-2">
            <div class="rounded-lg border border-[var(--border)] bg-white p-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 class="text-sm font-bold text-[var(--ink)]">Validation</h2>
                  <p class="mt-1 text-xs text-[var(--ink3)]">Errors block saving. Warnings keep IELTS timing tidy.</p>
                </div>
                <div class="flex gap-2">
                  <button class="ct-btn" @click="previewPayload">Preview JSON</button>
                  <button class="ct-btn ct-btn-accent" :disabled="saving || blockingErrors.length" @click="saveBuilder">{{ saving ? 'Saving...' : 'Save Speaking test' }}</button>
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

            <div class="rounded-lg border border-[var(--border)] bg-white p-4">
              <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 class="text-sm font-bold text-[var(--ink)]">Speaking preview</h2>
                <div class="flex gap-2">
                  <button
                    v-for="(part, idx) in builder.parts"
                    :key="idx"
                    class="rounded-full border px-3 py-1 text-xs font-semibold"
                    :class="previewPartIndex === idx ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-[var(--border)] text-[var(--ink3)]'"
                    @click="previewPartIndex = idx; previewQuestionIndex = 0"
                  >
                    {{ part.title || `Part ${idx + 1}` }}
                  </button>
                </div>
              </div>
              <div v-if="previewPart?.instruction_html" class="rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3">
                <p class="mb-2 text-xs font-semibold text-[var(--ink3)]">Instruction</p>
                <div class="prose prose-sm max-w-none" v-html="previewPart.instruction_html"></div>
              </div>
              <div class="mt-3 rounded-lg border border-[var(--border)] p-4">
                <div class="mb-3 flex flex-wrap gap-2">
                  <button
                    v-for="(question, idx) in previewPartQuestions"
                    :key="idx"
                    class="rounded-md border px-2 py-1 text-xs"
                    :class="previewQuestionIndex === idx ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-[var(--border)] text-[var(--ink3)]'"
                    @click="previewQuestionIndex = idx"
                  >
                    Q{{ idx + 1 }}
                  </button>
                </div>
                <p class="text-xs font-semibold text-[var(--ink3)]">Current question</p>
                <h3 class="mt-2 text-base font-bold text-[var(--ink)]">{{ previewQuestion?.title || 'No question' }}</h3>
                <div v-if="previewQuestion?.description" class="prose prose-sm mt-3 max-w-none text-[var(--ink2)]" v-html="previewQuestion.description"></div>
                <div class="mt-3 flex items-center gap-3 text-xs text-[var(--ink3)]">
                  <span>Think: {{ previewQuestion?.time_to_think || 0 }}s</span>
                  <span>Answer: {{ previewQuestion?.time_limit || 30 }}s</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div v-else class="space-y-3">
          <div class="flex justify-end gap-2">
            <button class="ct-btn btn-sm" @click="runSync">Cập nhật JSON</button>
            <button class="ct-btn btn-sm" @click="refreshRawPreview">Tải từ server</button>
          </div>
          <AdminJsonPanel v-model="rawText" module="speaking" tall :live="jsonLive" :syncing="jsonSyncing" />
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

const pageStyle = moduleStyle('speaking')

const activeTab = ref('builder')
const items = ref([])
const selectedId = ref(null)
const selectedPartIndex = ref(0)
const previewPartIndex = ref(0)
const previewQuestionIndex = ref(0)
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

const currentPart = computed(() => builder.parts[selectedPartIndex.value] || builder.parts[0])
const previewPart = computed(() => builder.parts[previewPartIndex.value] || builder.parts[0])
const previewPartQuestions = computed(() => previewPart.value?.questions || [])
const previewQuestion = computed(() => previewPartQuestions.value[previewQuestionIndex.value] || null)
const thumbnailPreview = computed(() => imageUrl(builder.thumbnail))
const totalQuestions = computed(() => builder.parts.reduce((sum, part) => sum + part.questions.length, 0))
const blockingErrors = computed(() => validateBuilder().errors)
const softWarnings = computed(() => validateBuilder().warnings)

const isArchived = computed(() => {
  if (!selectedId.value) return false
  const item = items.value.find(x => x.id === selectedId.value)
  return item && (item.status === 'archived' || item.status === 0)
})

function defaultInstruction(partNumber) {
  if (partNumber === 2) return '<ul><li>Part 2 will take about 3 to 4 minutes.</li><li>You will have 1 minute to prepare and 1 to 2 minutes to speak.</li></ul>'
  if (partNumber === 3) return '<ul><li>Part 3 will take about 4 to 5 minutes.</li><li>You will discuss more abstract questions related to Part 2.</li></ul>'
  return '<ul><li>Part 1 will take about 4 to 5 minutes.</li><li>The examiner will ask you general questions about familiar topics.</li></ul>'
}

function defaultsForPart(partNumber) {
  if (partNumber === 2) return { time_to_think: 60, time_limit: 120 }
  if (partNumber === 3) return { time_to_think: 0, time_limit: 45 }
  return { time_to_think: 0, time_limit: 30 }
}

function emptyBuilder() {
  return {
    id: null,
    title: 'New Speaking Mock Test',
    book_code: 'Admin',
    status: 'published',
    time: 13,
    thumbnail: '',
    parts: [1, 2, 3].map((n) => ({
      title: `Speaking Part ${n}`,
      time: n === 2 ? 3 : 5,
      instruction_html: defaultInstruction(n),
      questions: [emptyQuestion(n)],
    })),
  }
}

function emptyQuestion(partNumber) {
  return {
    title: '',
    description: '',
    ...defaultsForPart(partNumber),
    audio_url: '',
  }
}

function normalizeBuilder(payload) {
  const next = emptyBuilder()
  Object.assign(next, payload || {})
  next.parts = [0, 1, 2].map((idx) => {
    const source = next.parts?.[idx] || {}
    const partNumber = idx + 1
    return {
      title: source.title || `Speaking Part ${partNumber}`,
      time: Number(source.time || (partNumber === 2 ? 3 : 5)),
      instruction_html: source.instruction_html || defaultInstruction(partNumber),
      questions: (source.questions || []).map((question) => ({
        title: question.title || '',
        description: question.description || '',
        time_to_think: Number(question.time_to_think ?? defaultsForPart(partNumber).time_to_think),
        time_limit: Number(question.time_limit || defaultsForPart(partNumber).time_limit),
        audio_url: question.audio_url || '',
      })),
    }
  })
  return next
}

function resetBuilder(next = emptyBuilder()) {
  Object.assign(builder, JSON.parse(JSON.stringify(next)))
  selectedPartIndex.value = 0
  previewPartIndex.value = 0
  previewQuestionIndex.value = 0
}

async function loadList() {
  const data = await adminService.listMockTests({ skill_id: 8, q: filters.q || undefined })
  items.value = data.items || []
}

async function selectItem(id) {
  pause()
  error.value = ''
  savedMessage.value = ''
  selectedId.value = id
  activeTab.value = 'builder'
  try {
    const data = await adminService.getSpeakingMockTestBuilder(id)
    resetBuilder(normalizeBuilder(data.builder))
    lastRawJson.value = data.raw_json
    rawText.value = JSON.stringify(data.raw_json, null, 2)
  } catch (err) {
    lastRawJson.value = null
    rawText.value = ''
    error.value = detailMessage(err, 'Cannot load this Speaking test.')
  } finally {
    resume()
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

function addQuestion() {
  const partNumber = selectedPartIndex.value + 1
  currentPart.value.questions.push(emptyQuestion(partNumber))
}

function removeQuestion(idx) {
  currentPart.value.questions.splice(idx, 1)
  previewQuestionIndex.value = Math.max(0, Math.min(previewQuestionIndex.value, currentPart.value.questions.length - 1))
}

function moveQuestion(idx, delta) {
  const target = idx + delta
  if (target < 0 || target >= currentPart.value.questions.length) return
  const [question] = currentPart.value.questions.splice(idx, 1)
  currentPart.value.questions.splice(target, 0, question)
}

function validateBuilder() {
  const errors = []
  const warnings = []
  if (!builder.title.trim()) errors.push('Title is required.')
  if (builder.parts.length !== 3) errors.push('Speaking test must have exactly 3 parts.')
  builder.parts.forEach((part, partIdx) => {
    if (!part.questions.length) errors.push(`Part ${partIdx + 1} needs at least one question.`)
    part.questions.forEach((question, qIdx) => {
      if (!String(question.title || '').trim()) errors.push(`Part ${partIdx + 1} question ${qIdx + 1} needs a title.`)
      if (!Number(question.time_limit || 0)) errors.push(`Part ${partIdx + 1} question ${qIdx + 1} needs an answer time.`)
    })
  })
  const part2 = builder.parts[1]
  if (part2?.questions?.length > 1) warnings.push('Part 2 usually has exactly one cue-card question.')
  if (part2?.questions?.some((question) => !String(question.description || '').trim())) warnings.push('Part 2 should include cue-card description HTML.')
  if (Number(builder.time) < 11 || Number(builder.time) > 15) warnings.push('Speaking full test time is usually close to 13 minutes.')
  return { errors, warnings }
}

function payload() {
  const cloned = JSON.parse(JSON.stringify(builder))
  cloned.time = Number(cloned.time || 13)
  cloned.parts = cloned.parts.map((part, partIdx) => ({
    title: part.title || `Speaking Part ${partIdx + 1}`,
    time: Number(part.time || (partIdx === 1 ? 3 : 5)),
    instruction_html: part.instruction_html || defaultInstruction(partIdx + 1),
    questions: (part.questions || []).map((question) => ({
      title: String(question.title || '').trim(),
      description: question.description || '',
      time_to_think: Number(question.time_to_think || 0),
      time_limit: Number(question.time_limit || defaultsForPart(partIdx + 1).time_limit),
      audio_url: question.audio_url || '',
    })),
  }))
  return cloned
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
      ? await adminService.updateSpeakingMockTestBuilder(selectedId.value, body)
      : await adminService.createSpeakingMockTestBuilder(body)
    selectedId.value = result.mock_test_id
    resetBuilder(normalizeBuilder(result.builder))
    lastRawJson.value = result.raw_json
    rawText.value = JSON.stringify(result.raw_json, null, 2)
    savedMessage.value = `Saved Speaking test #${result.mock_test_id}. Backups: ${result.backup_paths?.length || 0}`
    await loadList()
  } catch (err) {
    error.value = detailMessage(err, 'Cannot save Speaking builder.')
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
      savedMessage.value = 'Đã hiện lại đề Speaking.'
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
      savedMessage.value = 'Đã ẩn đề Speaking.'
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

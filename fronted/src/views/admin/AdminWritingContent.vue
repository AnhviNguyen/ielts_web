<template>
  <div class="mx-auto max-w-7xl space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Writing CMS</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Quan ly writing topics trong backend/data JSON.</p>
      </div>
      <button class="ct-btn ct-btn-accent" @click="newTopic">New topic</button>
    </div>

    <div class="rounded-lg border border-[var(--border)] bg-white p-3">
      <div class="grid gap-3 md:grid-cols-[1fr_160px_160px_120px]">
        <input v-model="filters.q" class="ct-input" placeholder="Search title" @keyup.enter="loadList" />
        <select v-model="filters.task_type" class="ct-input">
          <option value="">All tasks</option>
          <option value="1">Task 1</option>
          <option value="2">Task 2</option>
        </select>
        <select v-model="filters.status" class="ct-input">
          <option value="">All status</option>
          <option value="published">published</option>
          <option value="archived">archived</option>
        </select>
        <button class="ct-btn" @click="loadList">Filter</button>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-[420px_1fr]">
      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="max-h-[760px] overflow-y-auto">
          <button
            v-for="item in items"
            :key="item.id"
            class="block w-full border-b border-[var(--border)] px-4 py-3 text-left hover:bg-[var(--bg)]"
            :class="selectedId === item.id ? 'bg-emerald-50' : ''"
            @click="selectTopic(item.id)"
          >
            <div class="line-clamp-2 text-sm font-semibold text-[var(--ink)]">{{ item.title }}</div>
            <div class="mt-1 text-xs text-[var(--ink3)]">#{{ item.id }} · Task {{ item.writing_task_type || '?' }} · {{ item.status || 'published' }}</div>
          </button>
          <div v-if="!items.length" class="p-6 text-center text-sm text-[var(--ink3)]">No writing topics.</div>
        </div>
      </section>

      <section class="space-y-4">
        <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>
        <div v-if="savedMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ savedMessage }}</div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 class="text-sm font-bold text-[var(--ink)]">Writing topic editor</h2>
              <p class="mt-1 text-xs text-[var(--ink3)]">Fields map to the public Writing practice page.</p>
            </div>
            <span class="rounded-md bg-[var(--bg)] px-2 py-1 text-xs font-semibold text-[var(--ink2)]">{{ taskHelper }}</span>
          </div>

          <div class="mt-4 grid gap-4">
            <section class="grid gap-3 md:grid-cols-2">
              <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="form.title" class="ct-input mt-1 w-full" /></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Task type<select v-model.number="form.writing_task_type" class="ct-input mt-1 w-full"><option :value="1">Task 1</option><option :value="2">Task 2</option></select></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Status<input v-model="form.status" class="ct-input mt-1 w-full" /></label>
            </section>

            <section class="grid gap-3 md:grid-cols-[180px_1fr]">
              <div class="aspect-video overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg)]">
                <img v-if="graphPreviewUrl" :src="graphPreviewUrl" class="h-full w-full object-contain" alt="" />
                <div v-else class="flex h-full items-center justify-center text-center text-xs text-[var(--ink3)]">No graph image</div>
              </div>
              <div class="space-y-2">
                <div class="text-xs font-semibold text-[var(--ink3)]">Upload graph / illustration</div>
                <input type="file" accept="image/png,image/jpeg,image/webp" class="block w-full text-sm" @change="uploadGraphImage" />
                <div class="flex flex-wrap gap-2">
                  <button class="ct-btn btn-sm" :disabled="uploadingImage" @click="syncRawFromForm">{{ uploadingImage ? 'Uploading...' : 'Preview JSON' }}</button>
                  <button class="ct-btn btn-sm" :disabled="!form.graph_image" @click="clearGraphImage">Clear image</button>
                </div>
                <p class="text-xs text-[var(--ink3)]">Saved to <code>questions[0].writing_graph_image</code>. Topic thumbnail is left unchanged.</p>
              </div>
            </section>

            <section class="grid gap-3">
              <label class="text-xs font-semibold text-[var(--ink3)]">Prompt text<textarea v-model="form.prompt_text" class="ct-input mt-1 min-h-24 w-full"></textarea></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Prompt HTML<textarea v-model="form.prompt_html" class="ct-input mt-1 min-h-32 w-full font-mono text-xs"></textarea></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Instruction / guidance HTML<textarea v-model="form.instruction" class="ct-input mt-1 min-h-36 w-full font-mono text-xs"></textarea></label>
            </section>

            <section class="rounded-lg border border-[var(--border)]">
              <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
                <div>
                  <h3 class="text-sm font-bold text-[var(--ink)]">Logical frames</h3>
                  <p class="mt-1 text-xs text-[var(--ink3)]">Reference sections used by the writing practice helper.</p>
                </div>
                <button class="ct-btn btn-sm" @click="addFrame">Add frame</button>
              </div>
              <div class="divide-y divide-[var(--border)]">
                <div v-for="(frame, idx) in form.logical_frames" :key="frame.local_id" class="grid gap-3 p-4 lg:grid-cols-[80px_1fr_120px]">
                  <label class="text-xs font-semibold text-[var(--ink3)]">Sort<input v-model.number="frame.sort" type="number" min="1" class="ct-input mt-1 w-full" /></label>
                  <label class="text-xs font-semibold text-[var(--ink3)]">Name<input v-model="frame.name" class="ct-input mt-1 w-full" /></label>
                  <label class="flex items-end gap-2 text-xs font-semibold text-[var(--ink3)]"><input v-model="frame.is_toggle_on" type="checkbox" class="mb-3" /> Enabled</label>
                  <label class="lg:col-span-3 text-xs font-semibold text-[var(--ink3)]">HTML<textarea v-model="frame.value" class="ct-input mt-1 min-h-24 w-full font-mono text-xs"></textarea></label>
                  <div class="lg:col-span-3 flex justify-end"><button class="ct-btn btn-sm" @click="removeFrame(idx)">Remove</button></div>
                </div>
                <div v-if="!form.logical_frames.length" class="p-6 text-center text-sm text-[var(--ink3)]">No logical frames.</div>
              </div>
            </section>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <button class="ct-btn ct-btn-accent" @click="saveForm">Save form</button>
            <button class="ct-btn" @click="syncRawFromForm">Preview JSON</button>
            <button class="ct-btn" @click="saveRaw">Save raw JSON</button>
            <button v-if="selectedId" class="ct-btn" @click="archiveTopic">Archive</button>
          </div>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-sm font-bold text-[var(--ink)]">Practice preview</h2>
            <span class="text-xs text-[var(--ink3)]">Prompt + graph + guidance</span>
          </div>
          <div class="rounded-xl border border-[var(--border)] p-5">
            <div v-if="form.prompt_html" class="prose prose-sm max-w-none text-sm leading-relaxed text-[var(--ink)]" v-html="form.prompt_html"></div>
            <p v-else class="text-sm text-[var(--ink3)]">{{ form.prompt_text || 'No prompt yet.' }}</p>
            <div v-if="graphPreviewUrl" class="mt-4 overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg)]">
              <img :src="graphPreviewUrl" class="max-h-[420px] w-full object-contain" alt="" />
            </div>
            <details v-if="form.instruction" class="mt-4 rounded-lg border border-[var(--border)] bg-[var(--bg)]">
              <summary class="cursor-pointer px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#34d399]">Guidance</summary>
              <div class="px-4 pb-4 pt-2 text-sm leading-relaxed text-[var(--ink)]" v-html="form.instruction"></div>
            </details>
          </div>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="mb-2 flex items-center justify-between">
            <h2 class="text-sm font-bold text-[var(--ink)]">Raw JSON</h2>
            <span class="text-xs text-[var(--ink3)]">Validated with JSON.parse before save</span>
          </div>
          <textarea v-model="rawText" class="ct-input min-h-[420px] w-full font-mono text-xs"></textarea>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'
import { imageUrl } from '@/utils/mediaUrl.js'

const items = ref([])
const selectedId = ref(null)
const rawText = ref('')
const error = ref('')
const savedMessage = ref('')
const uploadingImage = ref(false)
const filters = reactive({ q: '', task_type: '', status: '' })
const form = reactive({
  title: '',
  writing_task_type: 1,
  status: 'published',
  graph_image: '',
  prompt_text: '',
  prompt_html: '',
  instruction: '',
  logical_frames: [],
})

const graphPreviewUrl = computed(() => imageUrl(form.graph_image))
const taskHelper = computed(() => Number(form.writing_task_type) === 2 ? 'Task 2 - 40 min - 250+ words' : 'Task 1 - 20 min - 150+ words')

function setRaw(raw) {
  rawText.value = JSON.stringify(raw, null, 2)
}

function parseRaw() {
  try {
    return JSON.parse(rawText.value)
  } catch {
    throw new Error('Raw JSON invalid.')
  }
}

function fillForm(item) {
  const question = (item.questions || [])[0] || {}
  Object.assign(form, {
    title: item.title || '',
    writing_task_type: Number(item.writing_task_type || 1),
    status: item.status || 'published',
    graph_image: question.writing_graph_image || item.writing_graph_image || '',
    prompt_text: question.title || item.prompt_text || '',
    prompt_html: question.content_writing || item.prompt_html || '',
    instruction: question.instruction || '',
    logical_frames: normalizeFrames(question.writing_logical_frame || []),
  })
}

function applyForm(raw) {
  const wrapper = raw.data ? raw : { code: 0, message: '', data: raw }
  const item = wrapper.data
  item.title = form.title
  item.writing_task_type = Number(form.writing_task_type || 1)
  item.status = form.status || 'published'
  item.is_public = item.status !== 'archived'
  item.questions = Array.isArray(item.questions) && item.questions.length ? item.questions : [emptyQuestion(item.id)]
  const question = item.questions[0]
  question.quiz_id = item.id || question.quiz_id
  question.type = question.type || 'writing'
  question.status = question.status || 'published'
  question.order = question.order || 1
  question.title = form.prompt_text
  question.content_writing = form.prompt_html
  question.instruction = form.instruction || ''
  question.writing_graph_image = form.graph_image || ''
  question.writing_logical_frame = form.logical_frames
    .slice()
    .sort((a, b) => Number(a.sort || 0) - Number(b.sort || 0))
    .map((frame, idx) => ({
      id: frame.id || Date.now() + idx,
      sort: Number(frame.sort || idx + 1),
      name: frame.name || `Frame ${idx + 1}`,
      value: frame.value || '',
      question_id: question.id,
      is_toggle_on: Boolean(frame.is_toggle_on),
    }))
  wrapper.data = item
  return wrapper
}

function emptyQuestion(topicId) {
  return {
    id: Date.now(),
    quiz_id: topicId,
    type: 'writing',
    title: '',
    status: 'published',
    content_writing: '',
    order: 1,
    instruction: '',
    writing_graph_image: '',
    writing_logical_frame: [],
  }
}

function normalizeFrames(frames) {
  return (Array.isArray(frames) ? frames : [])
    .slice()
    .sort((a, b) => Number(a?.sort || 0) - Number(b?.sort || 0))
    .map((frame, idx) => ({
      local_id: `${frame?.id || 'new'}_${idx}_${Date.now()}`,
      id: frame?.id || null,
      sort: Number(frame?.sort || idx + 1),
      name: frame?.name || `Frame ${idx + 1}`,
      value: frame?.value || '',
      is_toggle_on: frame?.is_toggle_on !== false,
    }))
}

function addFrame() {
  const nextSort = form.logical_frames.length + 1
  form.logical_frames.push({
    local_id: `new_${Date.now()}_${nextSort}`,
    id: null,
    sort: nextSort,
    name: nextSort === 1 ? 'Introduction' : `Frame ${nextSort}`,
    value: '',
    is_toggle_on: true,
  })
}

function removeFrame(idx) {
  form.logical_frames.splice(idx, 1)
}

function syncRawFromForm() {
  try {
    setRaw(applyForm(parseRaw()))
    savedMessage.value = 'Raw JSON preview updated from form.'
  } catch (err) {
    error.value = err.message || 'Cannot preview JSON.'
  }
}

async function uploadGraphImage(event) {
  const file = event.target.files?.[0]
  if (!file) return
  error.value = ''
  savedMessage.value = ''
  uploadingImage.value = true
  try {
    const result = await adminService.uploadAdminImage(file)
    form.graph_image = result.id
    syncRawFromForm()
    savedMessage.value = 'Graph image uploaded.'
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Cannot upload graph image.'
  } finally {
    uploadingImage.value = false
    event.target.value = ''
  }
}

function clearGraphImage() {
  form.graph_image = ''
  syncRawFromForm()
}

async function loadList() {
  const params = {
    q: filters.q || undefined,
    task_type: filters.task_type || undefined,
    status: filters.status || undefined,
  }
  const data = await adminService.listWritingTopics(params)
  items.value = data.items
}

async function selectTopic(id) {
  error.value = ''
  savedMessage.value = ''
  const data = await adminService.getWritingTopic(id)
  selectedId.value = id
  setRaw(data.raw_json)
  fillForm(data.item)
}

function newTopic() {
  selectedId.value = null
  const raw = { code: 0, message: '', data: { title: 'New writing topic', status: 'published', writing_task_type: 1, questions: [emptyQuestion(null)], is_public: true } }
  setRaw(raw)
  fillForm(raw.data)
}

async function saveForm() {
  try {
    const raw = applyForm(parseRaw())
    const result = selectedId.value
      ? await adminService.updateWritingTopic(selectedId.value, raw)
      : await adminService.createWritingTopic(raw)
    selectedId.value = result.item.id
    setRaw(result.raw_json)
    fillForm(result.item)
    savedMessage.value = `Saved. Backup: ${result.backup_path || 'none'}`
    await loadList()
  } catch (err) {
    error.value = err.message || err.response?.data?.detail || 'Cannot save writing topic.'
  }
}

async function saveRaw() {
  try {
    const raw = parseRaw()
    const id = selectedId.value || raw.data?.id || raw.id
    const result = id ? await adminService.updateWritingTopic(id, raw) : await adminService.createWritingTopic(raw)
    selectedId.value = result.item.id
    setRaw(result.raw_json)
    fillForm(result.item)
    savedMessage.value = `Saved raw JSON. Backup: ${result.backup_path || 'none'}`
    await loadList()
  } catch (err) {
    error.value = err.message || err.response?.data?.detail || 'Cannot save raw JSON.'
  }
}

async function archiveTopic() {
  if (!selectedId.value || !window.confirm('Archive this writing topic?')) return
  const result = await adminService.archiveWritingTopic(selectedId.value)
  setRaw(result.raw_json)
  fillForm(result.item)
  savedMessage.value = 'Archived.'
  await loadList()
}

onMounted(async () => {
  await loadList()
  if (items.value.length) await selectTopic(items.value[0].id)
})
</script>

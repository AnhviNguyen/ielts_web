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
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="form.title" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Task type<select v-model.number="form.writing_task_type" class="ct-input mt-1 w-full"><option :value="1">Task 1</option><option :value="2">Task 2</option></select></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Status<input v-model="form.status" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Thumbnail/image id<input v-model="form.thumbnail" class="ct-input mt-1 w-full" /></label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Prompt text<textarea v-model="form.prompt_text" class="ct-input mt-1 min-h-24 w-full"></textarea></label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Prompt HTML<textarea v-model="form.prompt_html" class="ct-input mt-1 min-h-28 w-full font-mono text-xs"></textarea></label>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button class="ct-btn ct-btn-accent" @click="saveForm">Save form</button>
            <button class="ct-btn" @click="saveRaw">Save raw JSON</button>
            <button v-if="selectedId" class="ct-btn" @click="archiveTopic">Archive</button>
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
import { onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'

const items = ref([])
const selectedId = ref(null)
const rawText = ref('')
const error = ref('')
const savedMessage = ref('')
const filters = reactive({ q: '', task_type: '', status: '' })
const form = reactive({ title: '', writing_task_type: 1, status: 'published', thumbnail: '', prompt_text: '', prompt_html: '' })

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
    thumbnail: item.thumbnail || item.writing_graph_image || '',
    prompt_text: question.title || item.prompt_text || '',
    prompt_html: question.content_writing || item.prompt_html || '',
  })
}

function applyForm(raw) {
  const wrapper = raw.data ? raw : { code: 0, message: '', data: raw }
  const item = wrapper.data
  item.title = form.title
  item.writing_task_type = Number(form.writing_task_type || 1)
  item.status = form.status || 'published'
  item.thumbnail = form.thumbnail || ''
  item.is_public = item.status !== 'archived'
  item.questions = item.questions?.length ? item.questions : [{ id: Date.now(), quiz_id: item.id, type: 'writing' }]
  item.questions[0].title = form.prompt_text
  item.questions[0].content_writing = form.prompt_html
  wrapper.data = item
  return wrapper
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
  const raw = { code: 0, message: '', data: { title: 'New writing topic', status: 'published', writing_task_type: 1, questions: [{ type: 'writing', title: '', content_writing: '' }], is_public: true } }
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

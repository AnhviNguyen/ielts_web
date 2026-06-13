<template>
  <div class="admin-page mx-auto max-w-[1600px] space-y-5" :style="pageStyle">
    <AdminPageHeader module="translation" title="Translation CMS" subtitle="Quản lý Step → Topic → Sentence cho luyện dịch." />

    <AdminCrudBar
      module="translation"
      archive-label="Xóa"
      :can-archive="crudCanDelete"
      :saving="saving"
      @create="onCrudCreate"
      @save="onCrudSave"
      @archive="onCrudDelete"
      @refresh="onCrudRefresh"
    >
      <span class="text-xs font-semibold text-[var(--ink3)]">{{ crudLabel }}</span>
    </AdminCrudBar>

    <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>
    <div v-if="savedMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ savedMessage }}</div>

    <div class="grid min-h-[720px] gap-4 xl:grid-cols-[260px_280px_minmax(0,1fr)]">
      <!-- Steps -->
      <section class="flex flex-col overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg-surface)]">
        <div class="space-y-2 border-b border-[var(--border)] p-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-[var(--ink3)]">Steps</h2>
          <input v-model="filters.q" class="ct-input w-full" placeholder="Tìm step…" @keyup.enter="loadSteps" />
          <select v-model="filters.active" class="ct-input w-full" @change="loadSteps">
            <option value="">Tất cả</option>
            <option value="true">Active</option>
            <option value="false">Archived</option>
          </select>
        </div>
        <div class="flex-1 overflow-y-auto">
          <button
            v-for="step in steps"
            :key="step.id"
            class="block w-full border-b border-[var(--border)] px-3 py-3 text-left hover:bg-[var(--bg)]"
            :class="selectedStep?.id === step.id ? 'admin-list-active' : ''"
            @click="selectStep(step.id)"
          >
            <div class="flex items-start justify-between gap-2">
              <span class="text-sm font-semibold text-[var(--ink)]">{{ step.title }}</span>
              <span class="shrink-0 text-[10px] text-[var(--ink3)]">{{ step.topic_count }}T</span>
            </div>
            <div class="mt-1 text-[11px] text-[var(--ink3)]">{{ step.sentence_count }} câu · {{ step.is_active ? 'active' : 'archived' }}</div>
          </button>
          <div v-if="!steps.length" class="p-6 text-center text-sm text-[var(--ink3)]">Chưa có step.</div>
        </div>
      </section>

      <!-- Topics -->
      <section class="flex flex-col overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg-surface)]">
        <div class="flex items-center justify-between gap-2 border-b border-[var(--border)] px-3 py-3">
          <div class="min-w-0">
            <h2 class="text-xs font-bold uppercase tracking-wider text-[var(--ink3)]">Topics</h2>
            <p v-if="selectedStep" class="truncate text-[11px] text-[var(--ink3)]">{{ selectedStep.title }}</p>
          </div>
          <button class="ct-btn btn-sm shrink-0" :disabled="!selectedStep" @click="createTopic">+ Topic</button>
        </div>
        <div class="flex-1 overflow-y-auto">
          <template v-if="selectedStep">
            <div
              v-for="topic in topics"
              :key="topic.id"
              class="group flex items-start gap-2 border-b border-[var(--border)] px-3 py-3 hover:bg-[var(--bg)]"
              :class="selectedTopic?.id === topic.id ? 'admin-list-active' : ''"
            >
              <button class="min-w-0 flex-1 text-left" @click="selectTopic(topic.id)">
                <div class="text-sm font-semibold text-[var(--ink)]">{{ topic.title }}</div>
                <div class="mt-1 text-[11px] text-[var(--ink3)]">{{ topic.sentence_count }} câu · {{ topic.is_active ? 'active' : 'archived' }}</div>
              </button>
              <button
                type="button"
                class="ct-btn btn-sm shrink-0 opacity-70 group-hover:opacity-100"
                title="Xóa topic"
                @click.stop="deleteTopicById(topic.id)"
              >
                Xóa
              </button>
            </div>
            <div v-if="!topics.length" class="p-6 text-center text-sm text-[var(--ink3)]">Chưa có topic. Bấm + Topic để thêm.</div>
          </template>
          <div v-else class="p-6 text-center text-sm text-[var(--ink3)]">Chọn một step bên trái.</div>
        </div>
      </section>

      <!-- Detail workspace -->
      <section class="flex min-w-0 flex-col gap-4 overflow-hidden">
        <!-- Step editor -->
        <div v-if="!selectedStep || (!selectedTopic && detailMode === 'step')" class="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] p-4">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-sm font-bold text-[var(--ink)]">{{ selectedStep ? 'Chỉnh sửa step' : 'Tạo step mới' }}</h2>
            <button v-if="selectedStep && topics.length" class="ct-btn btn-sm" @click="detailMode = 'topic'">Quản lý topic →</button>
          </div>
          <div class="mt-3 grid gap-3 sm:grid-cols-2">
            <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="stepForm.title" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Order<input v-model.number="stepForm.order" type="number" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Badge<input v-model="stepForm.badge_label" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Badge color<input v-model="stepForm.badge_color" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Icon<input v-model="stepForm.icon_emoji" class="ct-input mt-1 w-full" /></label>
            <label class="flex items-center gap-2 pt-6 text-sm text-[var(--ink2)]"><input v-model="stepForm.is_active" type="checkbox" /> Active</label>
            <label class="sm:col-span-2 text-xs font-semibold text-[var(--ink3)]">Description<textarea v-model="stepForm.description" class="ct-input mt-1 min-h-20 w-full"></textarea></label>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button class="ct-btn ct-btn-accent" :disabled="saving" @click="saveStep">Lưu step</button>
            <button v-if="selectedStep" class="ct-btn" :disabled="saving" @click="deleteStep">Xóa step</button>
          </div>
        </div>

        <!-- Topic + Sentences -->
        <template v-if="selectedStep && (selectedTopic || detailMode === 'topic')">
          <div class="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="text-[11px] font-semibold uppercase tracking-wider text-[var(--ink3)]">{{ selectedStep.title }}</p>
                <h2 class="text-sm font-bold text-[var(--ink)]">{{ selectedTopic ? 'Chỉnh sửa topic' : 'Tạo topic mới' }}</h2>
              </div>
              <div class="flex flex-wrap gap-2">
                <button class="ct-btn btn-sm" @click="detailMode = 'step'">← Step</button>
                <button class="ct-btn btn-sm" :disabled="!selectedTopic" @click="createSentence">+ Câu</button>
                <button class="ct-btn ct-btn-accent btn-sm" :disabled="saving" @click="saveTopic">Lưu topic</button>
                <button v-if="selectedTopic" class="ct-btn btn-sm" :disabled="saving" @click="deleteTopic">Xóa topic</button>
              </div>
            </div>
            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="topicForm.title" class="ct-input mt-1 w-full" /></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Order<input v-model.number="topicForm.order" type="number" class="ct-input mt-1 w-full" /></label>
              <label class="sm:col-span-2 text-xs font-semibold text-[var(--ink3)]">Description<textarea v-model="topicForm.description" class="ct-input mt-1 min-h-16 w-full"></textarea></label>
              <label class="flex items-center gap-2 text-sm text-[var(--ink2)]"><input v-model="topicForm.is_active" type="checkbox" /> Active</label>
            </div>
          </div>

          <div v-if="selectedTopic" class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg-surface)]">
            <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
              <h2 class="text-sm font-bold text-[var(--ink)]">Sentences ({{ sentences.length }})</h2>
              <button class="ct-btn btn-sm" @click="createSentence">+ Thêm câu</button>
            </div>
            <div class="flex-1 overflow-auto">
              <table class="w-full min-w-[640px] text-left text-sm">
                <thead class="sticky top-0 z-10 bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
                  <tr>
                    <th class="px-3 py-2 w-10">#</th>
                    <th class="px-3 py-2">Tiếng Việt</th>
                    <th class="px-3 py-2">English</th>
                    <th class="px-3 py-2 w-16">TT</th>
                    <th class="px-3 py-2 w-28 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="sentence in sentences"
                    :key="sentence.id"
                    class="border-t border-[var(--border)] hover:bg-[var(--bg)]"
                    :class="sentenceForm.id === sentence.id && sentenceFormOpen ? 'bg-[var(--green-bg)]' : ''"
                  >
                    <td class="px-3 py-2 text-[var(--ink3)]">{{ sentence.order }}</td>
                    <td class="px-3 py-2 max-w-[200px] truncate" :title="sentence.vietnamese">{{ sentence.vietnamese }}</td>
                    <td class="px-3 py-2 max-w-[200px] truncate" :title="sentence.english">{{ sentence.english }}</td>
                    <td class="px-3 py-2 text-xs text-[var(--ink3)]">{{ sentence.is_active ? 'on' : 'off' }}</td>
                    <td class="px-3 py-2 text-right whitespace-nowrap">
                      <button class="ct-btn btn-sm" @click="editSentence(sentence)">Sửa</button>
                      <button class="ct-btn btn-sm ml-1" @click="deleteSentence(sentence)">Xóa</button>
                    </td>
                  </tr>
                  <tr v-if="!sentences.length">
                    <td colspan="5" class="px-4 py-8 text-center text-sm text-[var(--ink3)]">Chưa có câu nào. Bấm + Thêm câu.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="sentenceFormOpen" class="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] p-4">
            <div class="flex items-center justify-between gap-3">
              <h2 class="text-sm font-bold text-[var(--ink)]">{{ sentenceForm.id ? 'Sửa câu' : 'Thêm câu mới' }}</h2>
              <button class="ct-btn btn-sm" @click="sentenceFormOpen = false">Đóng</button>
            </div>
            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              <label class="sm:col-span-2 text-xs font-semibold text-[var(--ink3)]">Tiếng Việt<textarea v-model="sentenceForm.vietnamese" class="ct-input mt-1 min-h-20 w-full"></textarea></label>
              <label class="sm:col-span-2 text-xs font-semibold text-[var(--ink3)]">English<textarea v-model="sentenceForm.english" class="ct-input mt-1 min-h-20 w-full"></textarea></label>
              <label class="sm:col-span-2 text-xs font-semibold text-[var(--ink3)]">Giải thích<textarea v-model="sentenceForm.explanation" class="ct-input mt-1 min-h-16 w-full"></textarea></label>
              <label class="text-xs font-semibold text-[var(--ink3)]">Order<input v-model.number="sentenceForm.order" type="number" class="ct-input mt-1 w-full" /></label>
              <label class="flex items-center gap-2 pt-6 text-sm text-[var(--ink2)]"><input v-model="sentenceForm.is_active" type="checkbox" /> Active</label>
            </div>
            <div class="mt-4 flex gap-2">
              <button class="ct-btn ct-btn-accent" :disabled="saving" @click="saveSentence">{{ sentenceForm.id ? 'Cập nhật' : 'Thêm câu' }}</button>
              <button class="ct-btn" @click="sentenceFormOpen = false">Hủy</button>
            </div>
          </div>
        </template>

        <div
          v-else-if="selectedStep && !selectedTopic"
          class="flex flex-1 items-center justify-center rounded-lg border border-dashed border-[var(--border)] bg-[var(--bg-surface)] p-8 text-center text-sm text-[var(--ink3)]"
        >
          Chọn topic ở cột giữa hoặc bấm <strong class="text-[var(--ink)]">+ Topic</strong> để thêm mới.
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
import { moduleStyle } from '@/components/admin/adminModules.js'

const pageStyle = moduleStyle('translation')

const steps = ref([])
const topics = ref([])
const sentences = ref([])
const selectedStep = ref(null)
const selectedTopic = ref(null)
const detailMode = ref('topic')
const error = ref('')
const savedMessage = ref('')
const saving = ref(false)
const sentenceFormOpen = ref(false)
const filters = reactive({ q: '', active: '' })
const stepForm = reactive(emptyStep())
const topicForm = reactive(emptyTopic())
const sentenceForm = reactive(emptySentence())

const crudContext = computed(() => {
  if (sentenceFormOpen.value) return 'sentence'
  if (detailMode.value === 'topic' && selectedStep.value) return 'topic'
  return 'step'
})

const crudLabel = computed(() => {
  if (crudContext.value === 'sentence') return 'Đang thao tác: Câu'
  if (crudContext.value === 'topic') return 'Đang thao tác: Topic'
  return 'Đang thao tác: Step'
})

const crudCanDelete = computed(() => {
  if (crudContext.value === 'sentence') return !!sentenceForm.id
  if (crudContext.value === 'topic') return !!selectedTopic.value
  return !!selectedStep.value
})

function apiError(err, fallback) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((x) => x?.msg || JSON.stringify(x)).join('; ')
  }
  return fallback
}

function trimFormStrings(form, keys) {
  const out = { ...form }
  keys.forEach((key) => {
    if (typeof out[key] === 'string') out[key] = out[key].trim()
  })
  return out
}

function emptyStep() {
  return { title: '', description: '', badge_label: '', badge_color: 'gray', icon_emoji: '📝', order: 0, is_active: true }
}

function emptyTopic() {
  return { title: '', description: '', order: 0, is_active: true }
}

function emptySentence() {
  return { id: null, vietnamese: '', english: '', explanation: '', order: 0, is_active: true }
}

function params() {
  return {
    q: filters.q || undefined,
    active: filters.active === '' ? undefined : filters.active === 'true',
  }
}

function fillStep(step = null) {
  Object.assign(stepForm, emptyStep(), step || {})
}

function fillTopic(topic = null) {
  Object.assign(topicForm, emptyTopic(), topic || {})
}

function fillSentence(sentence = null) {
  Object.assign(sentenceForm, emptySentence(), sentence || {})
}

async function loadSteps() {
  error.value = ''
  steps.value = await adminService.listTranslationSteps(params())
  if (!selectedStep.value && steps.value.length) await selectStep(steps.value[0].id)
}

async function selectStep(id, { autoTopic = true } = {}) {
  const detail = await adminService.getTranslationStep(id)
  selectedStep.value = detail.step
  topics.value = detail.topics
  fillStep(detail.step)
  selectedTopic.value = null
  sentences.value = []
  fillTopic()
  fillSentence()
  sentenceFormOpen.value = false
  detailMode.value = topics.value.length ? 'topic' : 'step'
  if (autoTopic && topics.value.length) await selectTopic(topics.value[0].id)
}

async function selectTopic(id) {
  const detail = await adminService.getTranslationTopic(id)
  selectedTopic.value = detail.topic
  sentences.value = detail.sentences
  fillTopic(detail.topic)
  fillSentence()
  sentenceFormOpen.value = false
  detailMode.value = 'topic'
}

function createStep() {
  selectedStep.value = null
  selectedTopic.value = null
  topics.value = []
  sentences.value = []
  fillStep()
  fillTopic()
  fillSentence()
  sentenceFormOpen.value = false
  detailMode.value = 'step'
}

function createTopic() {
  if (!selectedStep.value) return
  selectedTopic.value = null
  sentences.value = []
  fillTopic({ order: topics.value.length })
  fillSentence()
  sentenceFormOpen.value = false
  detailMode.value = 'topic'
}

function createSentence() {
  if (!selectedTopic.value) {
    error.value = 'Lưu topic trước khi thêm câu.'
    return
  }
  fillSentence({ order: sentences.value.length })
  sentenceFormOpen.value = true
}

function editSentence(sentence) {
  fillSentence(sentence)
  sentenceFormOpen.value = true
}

function onCrudCreate() {
  if (crudContext.value === 'sentence') {
    createSentence()
    return
  }
  if (crudContext.value === 'topic') {
    createTopic()
    return
  }
  createStep()
}

function onCrudSave() {
  if (crudContext.value === 'sentence') {
    saveSentence()
    return
  }
  if (crudContext.value === 'topic') {
    saveTopic()
    return
  }
  saveStep()
}

async function onCrudDelete() {
  if (crudContext.value === 'sentence') {
    if (!sentenceForm.id) return
    await deleteSentence({ id: sentenceForm.id })
    return
  }
  if (crudContext.value === 'topic') {
    await deleteTopic()
    return
  }
  await deleteStep()
}

function onCrudRefresh() {
  if (crudContext.value === 'sentence' && selectedTopic.value) {
    selectTopic(selectedTopic.value.id)
    return
  }
  if (crudContext.value === 'topic' && selectedStep.value) {
    selectStep(selectedStep.value.id)
    return
  }
  loadSteps()
}

async function saveStep() {
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  const body = trimFormStrings(stepForm, ['title', 'description', 'badge_label', 'badge_color', 'icon_emoji'])
  if (!body.title) {
    error.value = 'Tiêu đề step không được để trống.'
    saving.value = false
    return
  }
  if (!body.description) {
    error.value = 'Mô tả step không được để trống.'
    saving.value = false
    return
  }
  try {
    const saved = selectedStep.value
      ? await adminService.updateTranslationStep(selectedStep.value.id, body)
      : await adminService.createTranslationStep(body)
    selectedStep.value = saved
    savedMessage.value = 'Đã lưu step.'
    await loadSteps()
    await selectStep(saved.id)
  } catch (err) {
    error.value = apiError(err, 'Không lưu được step.')
  } finally {
    saving.value = false
  }
}

async function deleteStep() {
  if (!selectedStep.value || !window.confirm('Xóa vĩnh viễn step này và toàn bộ topic/câu bên trong?')) return
  saving.value = true
  error.value = ''
  try {
    await adminService.deleteTranslationStep(selectedStep.value.id)
    selectedStep.value = null
    selectedTopic.value = null
    detailMode.value = 'step'
    savedMessage.value = 'Đã xóa step.'
    await loadSteps()
  } catch (err) {
    error.value = apiError(err, 'Không xóa được step.')
  } finally {
    saving.value = false
  }
}

async function saveTopic() {
  if (!selectedStep.value) return
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  const body = trimFormStrings(topicForm, ['title', 'description'])
  if (!body.title) {
    error.value = 'Tiêu đề topic không được để trống.'
    saving.value = false
    return
  }
  try {
    const saved = selectedTopic.value
      ? await adminService.updateTranslationTopic(selectedTopic.value.id, body)
      : await adminService.createTranslationTopic(selectedStep.value.id, body)
    savedMessage.value = 'Đã lưu topic.'
    await selectStep(selectedStep.value.id, { autoTopic: false })
    await selectTopic(saved.id)
  } catch (err) {
    error.value = apiError(err, 'Không lưu được topic.')
  } finally {
    saving.value = false
  }
}

async function deleteTopic() {
  if (!selectedTopic.value || !window.confirm('Xóa vĩnh viễn topic này và toàn bộ câu bên trong?')) return
  await deleteTopicById(selectedTopic.value.id)
}

async function deleteTopicById(id) {
  if (!window.confirm('Xóa vĩnh viễn topic này và toàn bộ câu bên trong?')) return
  saving.value = true
  error.value = ''
  try {
    await adminService.deleteTranslationTopic(id)
    selectedTopic.value = null
    sentences.value = []
    sentenceFormOpen.value = false
    savedMessage.value = 'Đã xóa topic.'
    await selectStep(selectedStep.value.id, { autoTopic: false })
  } catch (err) {
    error.value = apiError(err, 'Không xóa được topic.')
  } finally {
    saving.value = false
  }
}

async function saveSentence() {
  if (!selectedTopic.value) {
    error.value = 'Lưu topic trước khi thêm câu.'
    return
  }
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  const body = trimFormStrings(sentenceForm, ['vietnamese', 'english', 'explanation'])
  if (!body.vietnamese) {
    error.value = 'Câu tiếng Việt không được để trống.'
    saving.value = false
    return
  }
  if (!body.english) {
    error.value = 'Câu tiếng Anh không được để trống.'
    saving.value = false
    return
  }
  try {
    const payload = { ...body }
    delete payload.id
    if (sentenceForm.id) await adminService.updateTranslationSentence(sentenceForm.id, payload)
    else await adminService.createTranslationSentence(selectedTopic.value.id, payload)
    savedMessage.value = 'Đã lưu câu.'
    sentenceFormOpen.value = false
    await selectTopic(selectedTopic.value.id)
  } catch (err) {
    error.value = apiError(err, 'Không lưu được câu.')
  } finally {
    saving.value = false
  }
}

async function deleteSentence(sentence) {
  if (!window.confirm('Xóa vĩnh viễn câu này?')) return
  saving.value = true
  error.value = ''
  try {
    await adminService.deleteTranslationSentence(sentence.id)
    if (sentenceForm.id === sentence.id) sentenceFormOpen.value = false
    savedMessage.value = 'Đã xóa câu.'
    await selectTopic(selectedTopic.value.id)
  } catch (err) {
    error.value = apiError(err, 'Không xóa được câu.')
  } finally {
    saving.value = false
  }
}

onMounted(loadSteps)
</script>

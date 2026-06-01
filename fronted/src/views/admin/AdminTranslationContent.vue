<template>
  <div class="mx-auto max-w-7xl space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Translation CMS</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Quan ly Step, Topic va Sentence cho luyen dich.</p>
      </div>
      <button class="ct-btn ct-btn-accent" @click="createStep">New step</button>
    </div>

    <div class="grid gap-4 lg:grid-cols-[320px_1fr]">
      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="space-y-2 border-b border-[var(--border)] p-3">
          <input v-model="filters.q" class="ct-input w-full" placeholder="Search step" @keyup.enter="loadSteps" />
          <select v-model="filters.active" class="ct-input w-full" @change="loadSteps">
            <option value="">All status</option>
            <option value="true">Active</option>
            <option value="false">Archived</option>
          </select>
        </div>
        <div class="max-h-[740px] overflow-y-auto">
          <button
            v-for="step in steps"
            :key="step.id"
            class="block w-full border-b border-[var(--border)] px-4 py-3 text-left hover:bg-[var(--bg)]"
            :class="selectedStep?.id === step.id ? 'bg-emerald-50' : ''"
            @click="selectStep(step.id)"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="font-semibold text-[var(--ink)]">{{ step.title }}</span>
              <span class="text-xs text-[var(--ink3)]">{{ step.topic_count }} topics</span>
            </div>
            <div class="mt-1 text-xs text-[var(--ink3)]">{{ step.sentence_count }} sentences · {{ step.is_active ? 'active' : 'archived' }}</div>
          </button>
          <div v-if="!steps.length" class="p-6 text-center text-sm text-[var(--ink3)]">No translation steps found.</div>
        </div>
      </section>

      <section class="space-y-4">
        <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>
        <div v-if="savedMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ savedMessage }}</div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-sm font-bold text-[var(--ink)]">{{ selectedStep ? 'Step' : 'New step' }}</h2>
            <button v-if="selectedStep" class="ct-btn btn-sm" @click="createTopic">New topic</button>
          </div>
          <div class="mt-3 grid gap-3 md:grid-cols-2">
            <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="stepForm.title" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Order<input v-model.number="stepForm.order" type="number" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Badge label<input v-model="stepForm.badge_label" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Badge color<input v-model="stepForm.badge_color" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Icon<input v-model="stepForm.icon_emoji" class="ct-input mt-1 w-full" /></label>
            <label class="flex items-center gap-2 pt-6 text-sm text-[var(--ink2)]"><input v-model="stepForm.is_active" type="checkbox" /> Active</label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Description<textarea v-model="stepForm.description" class="ct-input mt-1 min-h-20 w-full"></textarea></label>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button class="ct-btn ct-btn-accent" :disabled="saving" @click="saveStep">Save step</button>
            <button v-if="selectedStep" class="ct-btn" :disabled="saving" @click="archiveStep">Archive step</button>
          </div>
        </div>

        <div v-if="selectedStep" class="grid gap-4 xl:grid-cols-[360px_1fr]">
          <div class="rounded-lg border border-[var(--border)] bg-white">
            <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
              <h2 class="text-sm font-bold text-[var(--ink)]">Topics</h2>
              <button class="ct-btn btn-sm" @click="createTopic">New</button>
            </div>
            <div class="max-h-[520px] overflow-y-auto">
              <button
                v-for="topic in topics"
                :key="topic.id"
                class="block w-full border-b border-[var(--border)] px-4 py-3 text-left hover:bg-[var(--bg)]"
                :class="selectedTopic?.id === topic.id ? 'bg-emerald-50' : ''"
                @click="selectTopic(topic.id)"
              >
                <div class="font-semibold text-[var(--ink)]">{{ topic.title }}</div>
                <div class="mt-1 text-xs text-[var(--ink3)]">{{ topic.sentence_count }} sentences · {{ topic.is_active ? 'active' : 'archived' }}</div>
              </button>
              <div v-if="!topics.length" class="p-6 text-center text-sm text-[var(--ink3)]">No topics in this step.</div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="rounded-lg border border-[var(--border)] bg-white p-4">
              <div class="flex items-center justify-between gap-3">
                <h2 class="text-sm font-bold text-[var(--ink)]">{{ selectedTopic ? 'Topic' : 'New topic' }}</h2>
                <button v-if="selectedTopic" class="ct-btn btn-sm" @click="createSentence">New sentence</button>
              </div>
              <div class="mt-3 grid gap-3 md:grid-cols-2">
                <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="topicForm.title" class="ct-input mt-1 w-full" /></label>
                <label class="text-xs font-semibold text-[var(--ink3)]">Order<input v-model.number="topicForm.order" type="number" class="ct-input mt-1 w-full" /></label>
                <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Description<textarea v-model="topicForm.description" class="ct-input mt-1 min-h-20 w-full"></textarea></label>
                <label class="flex items-center gap-2 text-sm text-[var(--ink2)]"><input v-model="topicForm.is_active" type="checkbox" /> Active</label>
              </div>
              <div class="mt-4 flex flex-wrap gap-2">
                <button class="ct-btn ct-btn-accent" :disabled="!selectedStep || saving" @click="saveTopic">Save topic</button>
                <button v-if="selectedTopic" class="ct-btn" :disabled="saving" @click="archiveTopic">Archive topic</button>
              </div>
            </div>

            <div v-if="selectedTopic" class="rounded-lg border border-[var(--border)] bg-white">
              <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
                <h2 class="text-sm font-bold text-[var(--ink)]">Sentences</h2>
                <button class="ct-btn btn-sm" @click="createSentence">New</button>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[760px] text-left text-sm">
                  <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
                    <tr><th class="px-4 py-2">VI</th><th class="px-4 py-2">EN</th><th class="px-4 py-2">Order</th><th class="px-4 py-2">Status</th><th class="px-4 py-2"></th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="sentence in sentences" :key="sentence.id" class="border-t border-[var(--border)]">
                      <td class="px-4 py-3">{{ sentence.vietnamese }}</td>
                      <td class="px-4 py-3">{{ sentence.english }}</td>
                      <td class="px-4 py-3">{{ sentence.order }}</td>
                      <td class="px-4 py-3">{{ sentence.is_active ? 'active' : 'archived' }}</td>
                      <td class="px-4 py-3 text-right">
                        <button class="ct-btn btn-sm" @click="editSentence(sentence)">Edit</button>
                        <button class="ct-btn btn-sm ml-2" @click="archiveSentence(sentence)">Archive</button>
                      </td>
                    </tr>
                    <tr v-if="!sentences.length"><td colspan="5" class="px-4 py-6 text-center text-sm text-[var(--ink3)]">No sentences in this topic.</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-if="sentenceFormOpen" class="rounded-lg border border-[var(--border)] bg-white p-4">
              <h2 class="text-sm font-bold text-[var(--ink)]">{{ sentenceForm.id ? 'Edit sentence' : 'New sentence' }}</h2>
              <div class="mt-3 grid gap-3 md:grid-cols-2">
                <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Vietnamese<textarea v-model="sentenceForm.vietnamese" class="ct-input mt-1 min-h-24 w-full"></textarea></label>
                <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">English<textarea v-model="sentenceForm.english" class="ct-input mt-1 min-h-24 w-full"></textarea></label>
                <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Explanation<textarea v-model="sentenceForm.explanation" class="ct-input mt-1 min-h-20 w-full"></textarea></label>
                <label class="text-xs font-semibold text-[var(--ink3)]">Order<input v-model.number="sentenceForm.order" type="number" class="ct-input mt-1 w-full" /></label>
                <label class="flex items-center gap-2 pt-6 text-sm text-[var(--ink2)]"><input v-model="sentenceForm.is_active" type="checkbox" /> Active</label>
              </div>
              <div class="mt-4 flex gap-2">
                <button class="ct-btn ct-btn-accent" :disabled="saving" @click="saveSentence">Save sentence</button>
                <button class="ct-btn" @click="sentenceFormOpen = false">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'

const steps = ref([])
const topics = ref([])
const sentences = ref([])
const selectedStep = ref(null)
const selectedTopic = ref(null)
const error = ref('')
const savedMessage = ref('')
const saving = ref(false)
const sentenceFormOpen = ref(false)
const filters = reactive({ q: '', active: '' })
const stepForm = reactive(emptyStep())
const topicForm = reactive(emptyTopic())
const sentenceForm = reactive(emptySentence())

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

async function selectStep(id) {
  const detail = await adminService.getTranslationStep(id)
  selectedStep.value = detail.step
  topics.value = detail.topics
  fillStep(detail.step)
  selectedTopic.value = null
  sentences.value = []
  fillTopic()
  fillSentence()
  sentenceFormOpen.value = false
  if (topics.value.length) await selectTopic(topics.value[0].id)
}

async function selectTopic(id) {
  const detail = await adminService.getTranslationTopic(id)
  selectedTopic.value = detail.topic
  sentences.value = detail.sentences
  fillTopic(detail.topic)
  fillSentence()
  sentenceFormOpen.value = false
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
}

function createTopic() {
  if (!selectedStep.value) return
  selectedTopic.value = null
  sentences.value = []
  fillTopic()
  fillSentence()
  sentenceFormOpen.value = false
}

function createSentence() {
  if (!selectedTopic.value) return
  fillSentence()
  sentenceFormOpen.value = true
}

function editSentence(sentence) {
  fillSentence(sentence)
  sentenceFormOpen.value = true
}

async function saveStep() {
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  try {
    const saved = selectedStep.value
      ? await adminService.updateTranslationStep(selectedStep.value.id, { ...stepForm })
      : await adminService.createTranslationStep({ ...stepForm })
    selectedStep.value = saved
    savedMessage.value = 'Step saved.'
    await loadSteps()
    await selectStep(saved.id)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Cannot save step.'
  } finally {
    saving.value = false
  }
}

async function archiveStep() {
  if (!selectedStep.value || !window.confirm('Archive this step?')) return
  await adminService.archiveTranslationStep(selectedStep.value.id)
  selectedStep.value = null
  await loadSteps()
}

async function saveTopic() {
  if (!selectedStep.value) return
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  try {
    const saved = selectedTopic.value
      ? await adminService.updateTranslationTopic(selectedTopic.value.id, { ...topicForm })
      : await adminService.createTranslationTopic(selectedStep.value.id, { ...topicForm })
    savedMessage.value = 'Topic saved.'
    await selectStep(selectedStep.value.id)
    await selectTopic(saved.id)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Cannot save topic.'
  } finally {
    saving.value = false
  }
}

async function archiveTopic() {
  if (!selectedTopic.value || !window.confirm('Archive this topic?')) return
  await adminService.archiveTranslationTopic(selectedTopic.value.id)
  await selectStep(selectedStep.value.id)
}

async function saveSentence() {
  if (!selectedTopic.value) return
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  try {
    const body = { ...sentenceForm }
    delete body.id
    if (sentenceForm.id) await adminService.updateTranslationSentence(sentenceForm.id, body)
    else await adminService.createTranslationSentence(selectedTopic.value.id, body)
    savedMessage.value = 'Sentence saved.'
    await selectTopic(selectedTopic.value.id)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Cannot save sentence.'
  } finally {
    saving.value = false
  }
}

async function archiveSentence(sentence) {
  if (!window.confirm('Archive this sentence?')) return
  await adminService.archiveTranslationSentence(sentence.id)
  await selectTopic(selectedTopic.value.id)
}

onMounted(loadSteps)
</script>

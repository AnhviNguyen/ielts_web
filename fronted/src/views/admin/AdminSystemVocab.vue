<template>
  <div class="mx-auto max-w-7xl space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">System vocabulary</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Quan ly topic mau va copy tu vao topic cua user.</p>
      </div>
      <button class="ct-btn ct-btn-accent" @click="createTopic">New topic</button>
    </div>

    <div class="grid gap-4 lg:grid-cols-[340px_1fr]">
      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="border-b border-[var(--border)] p-3">
          <input v-model="filters.q" class="ct-input w-full" placeholder="Search topic" @keyup.enter="loadTopics" />
        </div>
        <div class="max-h-[720px] overflow-y-auto">
          <button
            v-for="topic in topics"
            :key="topic.id"
            class="block w-full border-b border-[var(--border)] px-4 py-3 text-left hover:bg-[var(--bg)]"
            :class="selected?.id === topic.id ? 'bg-emerald-50' : ''"
            @click="selectTopic(topic.id)"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="font-semibold text-[var(--ink)]">{{ topic.name }}</span>
              <span class="text-xs text-[var(--ink3)]">{{ topic.word_count }} words</span>
            </div>
            <div class="mt-1 text-xs text-[var(--ink3)]">{{ topic.level || 'Any level' }} · {{ topic.is_active ? 'active' : 'hidden' }}</div>
          </button>
          <div v-if="!topics.length" class="p-6 text-center text-sm text-[var(--ink3)]">No system topics yet.</div>
        </div>
      </section>

      <section class="space-y-4">
        <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-xs font-semibold text-[var(--ink3)]">Name<input v-model="topicForm.name" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Level<input v-model="topicForm.level" class="ct-input mt-1 w-full" placeholder="B1, IELTS 6.5..." /></label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Description<textarea v-model="topicForm.description" class="ct-input mt-1 w-full min-h-20"></textarea></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Sort order<input v-model.number="topicForm.sort_order" type="number" class="ct-input mt-1 w-full" /></label>
            <label class="flex items-center gap-2 pt-6 text-sm text-[var(--ink2)]"><input v-model="topicForm.is_active" type="checkbox" /> Active</label>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button class="ct-btn ct-btn-accent" @click="saveTopic">Save topic</button>
            <button v-if="selected" class="ct-btn" @click="deleteTopic">Delete</button>
            <button v-if="selected" class="ct-btn" @click="copyToUser">Copy to user</button>
          </div>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-white">
          <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <h2 class="text-sm font-bold text-[var(--ink)]">Words</h2>
            <button class="ct-btn btn-sm" :disabled="!selected" @click="startWord()">New word</button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full min-w-[760px] text-left text-sm">
              <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
                <tr><th class="px-4 py-2">Word</th><th class="px-4 py-2">Type</th><th class="px-4 py-2">Meaning VI</th><th class="px-4 py-2">Order</th><th class="px-4 py-2"></th></tr>
              </thead>
              <tbody>
                <tr v-for="word in words" :key="word.id" class="border-t border-[var(--border)]">
                  <td class="px-4 py-3 font-semibold">{{ word.word }}</td>
                  <td class="px-4 py-3">{{ word.word_type || '-' }}</td>
                  <td class="px-4 py-3">{{ word.meaning_vi || '-' }}</td>
                  <td class="px-4 py-3">{{ word.sort_order }}</td>
                  <td class="px-4 py-3 text-right">
                    <button class="ct-btn btn-sm" @click="startWord(word)">Edit</button>
                    <button class="ct-btn btn-sm ml-2" @click="deleteWord(word)">Delete</button>
                  </td>
                </tr>
                <tr v-if="!words.length"><td colspan="5" class="px-4 py-6 text-center text-sm text-[var(--ink3)]">No words in this topic.</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="wordFormOpen" class="rounded-lg border border-[var(--border)] bg-white p-4">
          <h2 class="text-sm font-bold text-[var(--ink)]">{{ wordForm.id ? 'Edit word' : 'New word' }}</h2>
          <div class="mt-3 grid gap-3 md:grid-cols-2">
            <input v-model="wordForm.word" class="ct-input" placeholder="Word" />
            <input v-model="wordForm.phonetic" class="ct-input" placeholder="Phonetic" />
            <input v-model="wordForm.word_type" class="ct-input" placeholder="Word type" />
            <input v-model.number="wordForm.sort_order" type="number" class="ct-input" placeholder="Sort order" />
            <textarea v-model="wordForm.meaning_en" class="ct-input min-h-20" placeholder="Meaning EN"></textarea>
            <textarea v-model="wordForm.meaning_vi" class="ct-input min-h-20" placeholder="Meaning VI"></textarea>
            <textarea v-model="wordForm.example" class="ct-input min-h-20" placeholder="Example"></textarea>
            <textarea v-model="wordForm.example_vi" class="ct-input min-h-20" placeholder="Example VI"></textarea>
          </div>
          <div class="mt-4 flex gap-2">
            <button class="ct-btn ct-btn-accent" @click="saveWord">Save word</button>
            <button class="ct-btn" @click="wordFormOpen = false">Cancel</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'

const topics = ref([])
const selected = ref(null)
const words = ref([])
const error = ref('')
const filters = reactive({ q: '' })
const topicForm = reactive({ name: '', description: '', level: '', sort_order: 0, is_active: true })
const wordFormOpen = ref(false)
const wordForm = reactive(emptyWord())

function emptyWord() {
  return { id: null, word: '', phonetic: '', word_type: '', meaning_en: '', meaning_vi: '', example: '', example_vi: '', tags: [], sort_order: 0 }
}

function fillTopic(topic = null) {
  Object.assign(topicForm, topic || { name: '', description: '', level: '', sort_order: 0, is_active: true })
}

function fillWord(word = null) {
  Object.assign(wordForm, emptyWord(), word || {})
}

async function loadTopics() {
  error.value = ''
  topics.value = await adminService.listSystemVocabTopics({ q: filters.q || undefined })
  if (!selected.value && topics.value.length) await selectTopic(topics.value[0].id)
}

async function selectTopic(id) {
  const detail = await adminService.getSystemVocabTopic(id)
  selected.value = detail.topic
  words.value = detail.words
  fillTopic(detail.topic)
  wordFormOpen.value = false
}

function createTopic() {
  selected.value = null
  words.value = []
  fillTopic()
}

async function saveTopic() {
  try {
    const body = { ...topicForm }
    const saved = selected.value
      ? await adminService.updateSystemVocabTopic(selected.value.id, body)
      : await adminService.createSystemVocabTopic(body)
    selected.value = saved
    await loadTopics()
    await selectTopic(saved.id)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Cannot save topic.'
  }
}

async function deleteTopic() {
  if (!selected.value || !window.confirm('Delete this system topic?')) return
  await adminService.deleteSystemVocabTopic(selected.value.id)
  selected.value = null
  words.value = []
  await loadTopics()
}

function startWord(word = null) {
  if (!selected.value) return
  fillWord(word)
  wordFormOpen.value = true
}

async function saveWord() {
  if (!selected.value) return
  const body = { ...wordForm }
  delete body.id
  if (wordForm.id) await adminService.updateSystemVocabWord(selected.value.id, wordForm.id, body)
  else await adminService.createSystemVocabWord(selected.value.id, body)
  await selectTopic(selected.value.id)
}

async function deleteWord(word) {
  if (!selected.value || !window.confirm(`Delete "${word.word}"?`)) return
  await adminService.deleteSystemVocabWord(selected.value.id, word.id)
  await selectTopic(selected.value.id)
}

async function copyToUser() {
  if (!selected.value) return
  const userId = window.prompt('Target user ID?')
  if (!userId) return
  const topicName = window.prompt('Target topic name?', selected.value.name) || selected.value.name
  const result = await adminService.copySystemVocabToUser(selected.value.id, { user_id: Number(userId), target_topic_name: topicName })
  window.alert(`Copied ${result.copied}, skipped ${result.skipped_duplicates}.`)
}

onMounted(loadTopics)
</script>

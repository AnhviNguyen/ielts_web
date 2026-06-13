<template>
  <div class="admin-page mx-auto max-w-7xl space-y-5" :style="pageStyle">
    <AdminPageHeader module="conversation" title="Conversation CMS" subtitle="Quản lý kịch bản role-play cho Conversation Practice." />

    <AdminCrudBar
      module="conversation"
      :can-archive="!!selected"
      :saving="saving"
      @create="createTopic"
      @save="saveTopic"
      @archive="archiveTopic"
      @refresh="loadTopics"
    />

    <div class="grid gap-4 lg:grid-cols-[360px_1fr]">
      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="space-y-2 border-b border-[var(--border)] p-3">
          <input v-model="filters.q" class="ct-input w-full" placeholder="Search scenario" @keyup.enter="loadTopics" />
          <div class="grid grid-cols-2 gap-2">
            <select v-model="filters.level" class="ct-input" @change="loadTopics">
              <option value="">All levels</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
            <select v-model="filters.active" class="ct-input" @change="loadTopics">
              <option value="">All status</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </div>
        </div>
        <div class="max-h-[740px] overflow-y-auto">
          <button
            v-for="topic in topics"
            :key="topic.id"
            class="block w-full border-b border-[var(--border)] px-4 py-3 text-left hover:bg-[var(--bg)]"
            :class="selected?.id === topic.id ? 'admin-list-active' : ''"
            @click="selectTopic(topic.id)"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="font-semibold text-[var(--ink)]">{{ topic.title }}</span>
              <span class="text-xs text-[var(--ink3)]">{{ topic.session_count }} sessions</span>
            </div>
            <div class="mt-1 text-xs text-[var(--ink3)]">{{ topic.level }} · {{ topic.is_active ? 'active' : 'archived' }}</div>
          </button>
          <div v-if="!topics.length" class="p-6 text-center text-sm text-[var(--ink3)]">No scenarios found.</div>
        </div>
      </section>

      <section class="space-y-4">
        <div v-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ error }}</div>
        <div v-if="savedMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ savedMessage }}</div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-xs font-semibold text-[var(--ink3)]">Title<input v-model="form.title" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Level
              <select v-model="form.level" class="ct-input mt-1 w-full">
                <option value="beginner">beginner</option>
                <option value="intermediate">intermediate</option>
                <option value="advanced">advanced</option>
              </select>
            </label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Order<input v-model.number="form.order" type="number" class="ct-input mt-1 w-full" /></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">Icon<input v-model="form.icon_emoji" class="ct-input mt-1 w-full" /></label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Description<textarea v-model="form.description" class="ct-input mt-1 min-h-20 w-full"></textarea></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">AI role<textarea v-model="form.ai_role" class="ct-input mt-1 min-h-24 w-full"></textarea></label>
            <label class="text-xs font-semibold text-[var(--ink3)]">User role<textarea v-model="form.user_role" class="ct-input mt-1 min-h-24 w-full"></textarea></label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Scenario<textarea v-model="form.scenario" class="ct-input mt-1 min-h-28 w-full"></textarea></label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Opening line<textarea v-model="form.opening_line" class="ct-input mt-1 min-h-24 w-full"></textarea></label>
            <label class="md:col-span-2 text-xs font-semibold text-[var(--ink3)]">Vocabulary, one phrase per line<textarea v-model="vocabularyText" class="ct-input mt-1 min-h-32 w-full"></textarea></label>
            <label class="flex items-center gap-2 pt-2 text-sm text-[var(--ink2)]"><input v-model="form.is_active" type="checkbox" /> Active</label>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button class="ct-btn ct-btn-accent" :disabled="saving" @click="saveTopic">{{ saving ? 'Saving...' : 'Save scenario' }}</button>
            <button v-if="selected" class="ct-btn" :disabled="saving" @click="archiveTopic">Archive</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { adminService } from '@/services/adminService.js'
import AdminCrudBar from '@/components/admin/AdminCrudBar.vue'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import { moduleStyle } from '@/components/admin/adminModules.js'

const pageStyle = moduleStyle('conversation')

const topics = ref([])
const selected = ref(null)
const vocabularyText = ref('')
const error = ref('')
const savedMessage = ref('')
const saving = ref(false)
const filters = reactive({ q: '', level: '', active: '' })
const form = reactive(emptyTopic())

function emptyTopic() {
  return {
    title: '',
    description: '',
    level: 'beginner',
    icon_emoji: '💬',
    ai_role: '',
    user_role: '',
    scenario: '',
    opening_line: '',
    order: 0,
    is_active: true,
  }
}

function fillForm(topic = null) {
  Object.assign(form, emptyTopic(), topic || {})
  vocabularyText.value = (topic?.vocabulary || []).join('\n')
}

function params() {
  return {
    q: filters.q || undefined,
    level: filters.level || undefined,
    active: filters.active === '' ? undefined : filters.active === 'true',
  }
}

async function loadTopics() {
  error.value = ''
  topics.value = await adminService.listConversationTopics(params())
  if (!selected.value && topics.value.length) await selectTopic(topics.value[0].id)
}

async function selectTopic(id) {
  selected.value = await adminService.getConversationTopic(id)
  fillForm(selected.value)
}

function createTopic() {
  selected.value = null
  fillForm()
  savedMessage.value = ''
}

function body() {
  return {
    ...form,
    vocabulary: vocabularyText.value.split('\n').map((x) => x.trim()).filter(Boolean),
  }
}

async function saveTopic() {
  saving.value = true
  error.value = ''
  savedMessage.value = ''
  try {
    const saved = selected.value
      ? await adminService.updateConversationTopic(selected.value.id, body())
      : await adminService.createConversationTopic(body())
    selected.value = saved
    savedMessage.value = 'Scenario saved.'
    await loadTopics()
    await selectTopic(saved.id)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Cannot save scenario.'
  } finally {
    saving.value = false
  }
}

async function archiveTopic() {
  if (!selected.value || !window.confirm('Archive this scenario?')) return
  await adminService.archiveConversationTopic(selected.value.id)
  selected.value = null
  fillForm()
  await loadTopics()
}

onMounted(loadTopics)
</script>

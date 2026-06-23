<template>
  <div class="hub-page">
    <section class="section-compact">
      <div class="app-container">
        <div class="spotify-panel">
          <div class="spotify-panel__header" data-tour="page-header">
            <div class="mb-3 inline-flex items-center gap-2 rounded-full border border-[var(--spotify-green)] bg-[var(--green-bg)] px-3 py-1.5">
              <span class="text-[var(--text-badge)] font-bold uppercase tracking-widest text-[var(--spotify-green)]">Speaking Practice</span>
            </div>
            <h1 class="font-display">AI <span class="text-[var(--spotify-green)]">Conversation</span></h1>
            <p class="page-subtitle max-w-xl">
              Role-play thực tế với AI — luyện ngữ pháp, từ vựng và phát âm qua hội thoại có ngữ cảnh.
            </p>
          </div>
          <div class="spotify-panel__body">
        <div class="mb-6 flex flex-wrap gap-2">
          <button
            v-for="opt in levelOptions"
            :key="opt.value"
            class="rounded-full px-4 py-1.5 text-[var(--text-button)] font-semibold transition-[background,color,border-color] duration-200 ease-in-out"
            :class="activeLevel === opt.value
              ? 'bg-[var(--spotify-green)] text-black'
              : 'border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--ink2)] hover:border-[var(--spotify-green)]'"
            @click="activeLevel = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>

        <div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="i in 6" :key="i" class="h-40 animate-pulse rounded-2xl bg-[var(--bg-interactive)]" />
        </div>

        <div v-else-if="error" class="py-16 text-center text-[var(--text-caption)] text-[var(--ink3)]">{{ error }}</div>

        <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-tour="test-grid">
          <button
            v-for="topic in filteredTopics"
            :key="topic.id"
            class="group rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)] p-5 text-left transition-[border-color,box-shadow] duration-200 ease-in-out hover:border-[var(--spotify-green)] hover:shadow-[var(--shadow-medium)] disabled:opacity-60"
            :disabled="starting === topic.id"
            @click="startTopic(topic.id)"
          >
            <div class="mb-3 flex items-start justify-between">
              <span class="text-2xl">{{ topic.icon_emoji || '💬' }}</span>
              <span
                class="rounded-full px-2 py-0.5 text-[var(--text-badge)] font-bold uppercase tracking-wider"
                :class="levelBadgeClass(topic.level)"
              >
                {{ levelLabel(topic.level) }}
              </span>
            </div>
            <h3 class="mb-1 text-[var(--text-feature)] font-semibold text-[var(--ink)] transition-colors duration-200 ease-in-out group-hover:text-[var(--spotify-green)]">
              {{ topic.title }}
            </h3>
            <p class="mb-3 line-clamp-2 text-[var(--text-caption)] text-[var(--ink2)]">{{ topic.description }}</p>
            <p class="text-[var(--text-small)] text-[var(--ink3)]">
              Bạn là: <span class="text-[var(--ink2)]">{{ shortRole(topic.user_role) }}</span>
            </p>
          </button>
        </div>
          </div>
        </div>
      </div>
    </section>
    <AiKeyRequiredModal :open="showGate" @close="goBack" @profile="goToProfile" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchTopics, LEVEL_LABELS } from '@/services/conversationService.js'
import { useAiKeyGate } from '@/composables/useAiKeyGate.js'
import AiKeyRequiredModal from '@/components/ui/AiKeyRequiredModal.vue'

const router = useRouter()
const { showGate, checkAiKey, goToProfile, goBack } = useAiKeyGate()
const loading = ref(true)
const error = ref('')
const topics = ref([])
const activeLevel = ref('all')
const starting = ref(null)

const levelOptions = [
  { value: 'all', label: 'Tất cả' },
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
]

const filteredTopics = computed(() =>
  activeLevel.value === 'all'
    ? topics.value
    : topics.value.filter(t => t.level === activeLevel.value)
)

function levelLabel(level) {
  return LEVEL_LABELS[level]?.label || level
}

function levelBadgeClass(level) {
  const map = {
    beginner: 'bg-[var(--green-bg)] text-[var(--spotify-green)]',
    intermediate: 'bg-[var(--blue-bg)] text-[var(--blue)]',
    advanced: 'bg-[var(--violet-bg)] text-[var(--violet)]',
  }
  return map[level] || 'bg-[var(--bg-interactive)] text-[var(--ink3)]'
}

function shortRole(role) {
  if (!role) return ''
  return role.length > 50 ? role.slice(0, 50) + '…' : role
}

async function startTopic(topicId) {
  const ok = await checkAiKey()
  if (!ok) return
  starting.value = topicId
  router.push(`/conversation/${topicId}`)
}

onMounted(async () => {
  await checkAiKey()
  try {
    topics.value = await fetchTopics()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Không tải được danh sách chủ đề.'
  } finally {
    loading.value = false
  }
})
</script>

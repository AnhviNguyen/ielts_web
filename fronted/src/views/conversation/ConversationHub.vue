<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-5xl mx-auto px-5 sm:px-8 pt-8 pb-16">

      <button
        @click="$router.push('/dashboard')"
        class="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors mb-8 group"
      >
        <svg class="group-hover:-translate-x-0.5 transition-transform" xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
        Dashboard
      </button>

      <div class="mb-8">
        <div class="inline-flex items-center gap-2 mb-3 px-3 py-1.5 rounded-full bg-emerald-50 border border-[#34d399]">
          <span class="text-xs font-bold tracking-widest uppercase text-emerald-700">Speaking Practice</span>
        </div>
        <h1 class="text-3xl sm:text-4xl font-black text-gray-900 mb-2">
          AI <span class="text-[#34d399]">Conversation</span>
        </h1>
        <p class="text-gray-500 max-w-xl">
          Role-play thực tế với AI — luyện ngữ pháp, từ vựng và phát âm qua hội thoại có ngữ cảnh.
        </p>
      </div>

      <!-- Level filter -->
      <div class="flex flex-wrap gap-2 mb-6">
        <button
          v-for="opt in levelOptions"
          :key="opt.value"
          @click="activeLevel = opt.value"
          class="px-4 py-1.5 rounded-full text-sm font-semibold transition-colors"
          :class="activeLevel === opt.value
            ? 'bg-gray-900 text-white'
            : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'"
        >
          {{ opt.label }}
        </button>
      </div>

      <div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in 6" :key="i" class="h-40 rounded-2xl bg-gray-200 animate-pulse" />
      </div>

      <div v-else-if="error" class="text-center py-16 text-gray-400">{{ error }}</div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <button
          v-for="topic in filteredTopics"
          :key="topic.id"
          @click="startTopic(topic.id)"
          :disabled="starting === topic.id"
          class="group text-left rounded-2xl border border-gray-200 bg-white p-5 hover:border-[#34d399] hover:shadow-md transition-all disabled:opacity-60"
        >
          <div class="flex items-start justify-between mb-3">
            <span class="text-2xl">{{ topic.icon_emoji || '💬' }}</span>
            <span
              class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
              :class="levelBadgeClass(topic.level)"
            >
              {{ levelLabel(topic.level) }}
            </span>
          </div>
          <h3 class="font-bold text-gray-900 mb-1 group-hover:text-[#059669] transition-colors">
            {{ topic.title }}
          </h3>
          <p class="text-sm text-gray-500 line-clamp-2 mb-3">{{ topic.description }}</p>
          <p class="text-xs text-gray-400">
            Bạn là: <span class="text-gray-600">{{ shortRole(topic.user_role) }}</span>
          </p>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchTopics, LEVEL_LABELS } from '@/services/conversationService.js'

const router = useRouter()
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
    beginner: 'bg-emerald-50 text-emerald-700',
    intermediate: 'bg-blue-50 text-blue-700',
    advanced: 'bg-purple-50 text-purple-700',
  }
  return map[level] || 'bg-gray-100 text-gray-600'
}

function shortRole(role) {
  if (!role) return ''
  return role.length > 50 ? role.slice(0, 50) + '…' : role
}

function startTopic(topicId) {
  starting.value = topicId
  router.push(`/conversation/${topicId}`)
}

onMounted(async () => {
  try {
    topics.value = await fetchTopics()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Không tải được danh sách chủ đề.'
  } finally {
    loading.value = false
  }
})
</script>

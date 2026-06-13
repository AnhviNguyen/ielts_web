<template>
  <div class="translation-step min-h-screen bg-[var(--bg-base)]">
    <div class="max-w-3xl mx-auto px-5 sm:px-8 pt-8 pb-16">

      <!-- Step hero banner -->
      <div v-if="currentStep" class="translation-step-hero relative rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)] p-6 sm:p-8 mb-8 overflow-hidden">
        <div class="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-[var(--green-bg)] opacity-60" aria-hidden="true" />
        <div class="absolute -right-4 top-12 h-20 w-20 rounded-full bg-[var(--green-bg)] opacity-40" aria-hidden="true" />

        <div class="relative">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-14 h-14 rounded-2xl border border-[var(--border)] bg-[var(--bg-interactive)] flex items-center justify-center">
              <svg v-html="heroIconPaths" v-bind="heroIconSvgAttrs" class="w-7 h-7"></svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-bold tracking-widest uppercase text-[var(--spotify-green-dark)]">Bước {{ currentStep.order }}</span>
                <span v-if="currentStep.badge_label" class="text-xs font-bold px-2 py-0.5 rounded-full bg-[var(--green-bg)] text-[var(--spotify-green-dark)]">
                  {{ currentStep.badge_label }}
                </span>
              </div>
              <h1 class="text-2xl sm:text-3xl font-black text-[var(--ink)] mb-2">{{ currentStep.title }}</h1>
              <p class="text-sm text-[var(--ink2)] leading-relaxed">{{ currentStep.description }}</p>
            </div>
          </div>

          <div class="flex gap-6 mt-5 pt-5 border-t border-[var(--border)]">
            <div>
              <p class="text-2xl font-black text-[var(--ink)]">{{ topics.length }}</p>
              <p class="text-xs text-[var(--ink3)] font-medium">Chủ đề</p>
            </div>
            <div>
              <p class="text-2xl font-black text-[var(--ink)]">{{ totalSentences }}</p>
              <p class="text-xs text-[var(--ink3)] font-medium">Câu dịch</p>
            </div>
            <div>
              <p class="text-2xl font-black text-[var(--ink)]">{{ completedTopics }}</p>
              <p class="text-xs text-[var(--ink3)] font-medium">Đã hoàn thành</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Step tab navigation -->
      <div v-if="allSteps.length" class="flex gap-2 flex-wrap mb-7">
        <button
          v-for="s in allSteps"
          :key="s.id"
          @click="switchStep(s.id)"
          :class="[
            'flex items-center gap-2 px-3 py-2 rounded-xl border-2 text-xs font-bold transition-all duration-150',
            s.id === currentStepId
              ? [tabActiveBorder(), tabActiveBg(), tabActiveText()]
              : 'border-[var(--border)] bg-[var(--bg-surface)] text-[var(--ink2)] hover:border-[var(--border2)] hover:bg-[var(--bg-interactive)]'
          ]"
        >
          <span class="opacity-70">{{ s.order }}</span>
          <span class="hidden sm:inline">{{ shortTitle(s.title) }}</span>
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 6" :key="i" class="h-20 rounded-2xl bg-[var(--bg-interactive)] animate-pulse"></div>
      </div>

      <!-- Topics grid -->
      <template v-else-if="topics.length">
        <div class="flex items-center justify-between mb-4">
          <p class="text-xs font-bold tracking-widest uppercase text-[var(--ink3)]">{{ topics.length }} chủ đề</p>
          <p v-if="completedTopics" class="text-xs font-semibold text-[var(--spotify-green)]">
            <svg class="inline w-3.5 h-3.5 mr-0.5 -mt-0.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ completedTopics }}/{{ topics.length }} đã học
          </p>
        </div>

        <div class="space-y-3">
          <article
            v-for="topic in topics"
            :key="topic.id"
            @click="goToPractice(topic.id)"
            :class="[
              'group relative flex items-center gap-4 p-4 sm:p-5 rounded-2xl border-2 bg-[var(--bg-surface)] cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-0.5',
              topic.completed_count > 0 && topic.completed_count >= topic.sentence_count
                ? 'border-[var(--spotify-green)]'
                : 'border-[var(--border)] hover:border-[var(--border2)]'
            ]"
          >
            <!-- Number badge -->
            <div :class="[
              'flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center text-base font-black transition-all',
              topic.completed_count > 0 ? topicNumBg.active : topicNumBg.idle
            ]">
              <svg v-if="topic.completed_count >= topic.sentence_count && topic.sentence_count > 0"
                class="w-5 h-5" style="color:#34d399"
                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span v-else class="topic-order" :class="topic.completed_count > 0 ? 'text-[var(--spotify-green)]' : 'text-[var(--ink2)]'">{{ topic.order }}</span>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <p class="topic-title text-sm sm:text-base font-bold mb-1 truncate">{{ topic.title }}</p>

              <!-- Progress bar -->
              <div class="flex items-center gap-2">
                <div class="flex-1 h-1.5 rounded-full bg-[var(--bg-interactive)] overflow-hidden">
                  <div
                    class="h-full rounded-full bg-[var(--spotify-green)] transition-all duration-500"
                    :style="{ width: progressWidth(topic) }"
                  ></div>
                </div>
                <span class="text-xs font-semibold text-[var(--ink3)] whitespace-nowrap">
                  {{ topic.completed_count }}/{{ topic.sentence_count }}
                </span>
              </div>
            </div>

            <!-- CTA -->
            <div class="flex-shrink-0 flex items-center gap-2">
              <span :class="[
                'hidden sm:inline-flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-full transition-all',
                topic.completed_count > 0
                  ? 'bg-[var(--green-bg)] text-[var(--spotify-green)] group-hover:brightness-110'
                  : 'bg-[var(--bg-interactive)] text-[var(--ink2)] group-hover:bg-[var(--bg2)]'
              ]">
                <svg v-if="topic.completed_count > 0" xmlns="http://www.w3.org/2000/svg" width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/>
                </svg>
                {{ topic.completed_count > 0 ? 'Tiếp tục' : 'Bắt đầu' }}
              </span>
              <svg class="text-[var(--ink3)] group-hover:text-[var(--ink2)] group-hover:translate-x-0.5 transition-all"
                xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 5l7 7-7 7"/>
              </svg>
            </div>
          </article>
        </div>

        <!-- Motivating tip card -->
        <div class="mt-8 p-5 rounded-2xl bg-[var(--green-bg)] border border-[var(--spotify-green)]/30">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 flex-shrink-0 rounded-xl bg-[var(--bg-surface)] border border-[var(--spotify-green)] flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="var(--spotify-green)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <div>
              <p class="text-sm font-bold text-[var(--ink)] mb-1">{{ motiveTip.title }}</p>
              <p class="text-sm text-[var(--ink2)] leading-relaxed">{{ motiveTip.body }}</p>
            </div>
          </div>
        </div>
      </template>

      <div v-else class="flex flex-col items-center gap-4 py-20 text-[var(--ink3)]">
        <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/>
        </svg>
        <p class="text-sm">Chưa có chủ đề nào.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchSteps, fetchTopics } from '@/services/translationService.js'

const route  = useRoute()
const router = useRouter()

const allSteps = ref([])
const topics   = ref([])
const loading  = ref(true)

const currentStepId = computed(() => Number(route.params.stepId))
const currentStep   = computed(() => allSteps.value.find(s => s.id === currentStepId.value))
const totalSentences   = computed(() => topics.value.reduce((s, t) => s + t.sentence_count, 0))
const completedTopics  = computed(() => topics.value.filter(t => t.completed_count > 0).length)

async function loadStep(id) {
  loading.value = true
  try { topics.value = await fetchTopics(id) }
  finally { loading.value = false }
}

function switchStep(id) { router.push(`/writing/translation/${id}`) }
function goToPractice(id) { router.push(`/writing/translation/practice/${id}`) }
function shortTitle(title) { return title.length > 18 ? title.slice(0, 18) + '…' : title }
function progressWidth(topic) {
  if (!topic.sentence_count) return '0%'
  return Math.round((topic.completed_count / topic.sentence_count) * 100) + '%'
}

// ── Hero icons ────────────────────────────────────────────────────────────────
const HERO_ICONS = [
  '<path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>',
  '<path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>',
  '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  '<path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4H4a1 1 0 00-1 1v2a4 4 0 004 4h1"/><path d="M17 4h3a1 1 0 011 1v2a4 4 0 01-4 4h-1"/><path d="M12 17a5 5 0 005-5V4H7v8a5 5 0 005 5z"/>',
  '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',
]

const heroIconPaths = computed(() => HERO_ICONS[(currentStep.value?.order ?? 1) - 1] ?? HERO_ICONS[0])
const heroIconSvgAttrs = {
  xmlns: 'http://www.w3.org/2000/svg',
  fill: 'none',
  viewBox: '0 0 24 24',
  stroke: 'var(--spotify-green)',
  'stroke-width': '2',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round',
}

// ── Tab active classes — unified green ────────────────────────────────────────
function tabActiveBorder()  { return 'border-[var(--spotify-green)]' }
function tabActiveBg()      { return 'bg-[var(--green-bg)]' }
function tabActiveText()    { return 'text-[var(--spotify-green-dark)]' }

// ── Topic number badge ────────────────────────────────────────────────────────
const topicNumBg = {
  idle:   'bg-[var(--bg-interactive)]',
  active: 'bg-[var(--green-bg)]',
}

// ── Motivational tips per step ────────────────────────────────────────────────
const TIPS = [
  { title: '💡 Cơ bản nhưng cực kỳ quan trọng!', body: 'Nền tảng ngữ pháp vững chắc là chìa khóa để viết câu Anh ngữ chính xác. Đừng bỏ qua bước này!' },
  { title: '🔥 Collocations = bí kíp Band 7+', body: 'Native speakers không học từ đơn, họ học cụm từ. Hãy luyện cho đến khi các collocation trở thành phản xạ tự nhiên.' },
  { title: '🎯 Band 6.5 trong tầm tay!', body: 'Mỗi đoạn văn bạn dịch được tốt hơn một chút là bạn đang tiến gần hơn đến mục tiêu. Hãy nhớ đọc lại đáp án mẫu!' },
  { title: '🏆 Band 8.0 — thử thách cao nhất!', body: 'Đây là nơi từ vựng C1-C2 phát huy tác dụng. Đừng ngại dùng những từ chưa quen — đó chính là cách học nhanh nhất.' },
  { title: '🎓 Essay hoàn chỉnh — bước cuối cùng!', body: 'Dịch được cả essay nghĩa là bạn đã nắm vững toàn bộ ngữ pháp và từ vựng cần thiết. Bạn đang rất gần đích rồi!' },
]

const motiveTip = computed(() => TIPS[(currentStep.value?.order ?? 1) - 1] ?? TIPS[0])

onMounted(async () => {
  allSteps.value = await fetchSteps()
  await loadStep(currentStepId.value)
})

watch(currentStepId, loadStep)
</script>

<style scoped>
.topic-title {
  color: var(--text-emphasis) !important;
}
.topic-order {
  font-weight: 800;
}
</style>

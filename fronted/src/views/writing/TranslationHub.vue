<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-3xl mx-auto px-5 sm:px-8 pt-8 pb-16">

      <!-- Back -->
      <button
        @click="$router.push('/writing')"
        class="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors mb-10 group"
      >
        <svg class="group-hover:-translate-x-0.5 transition-transform" xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
        </svg>
        Trở về Luyện Writing
      </button>

      <!-- Hero header -->
      <div class="mb-10">
        <div class="inline-flex items-center gap-2 mb-4 px-3 py-1.5 rounded-full bg-emerald-50 border border-[#34d399]">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/>
          </svg>
          <span class="text-xs font-bold tracking-widest uppercase" style="color:#059669">Translation Hub</span>
        </div>

        <h1 class="text-4xl sm:text-5xl font-black text-gray-900 leading-tight mb-4">
          Tập Dịch <span style="color:#34d399">IELTS</span>
        </h1>
        <p class="text-gray-500 text-base leading-relaxed max-w-xl mb-6">
          Từ câu đơn cơ bản đến essay Band 8.0+ — lộ trình được thiết kế để bạn tiến bộ rõ ràng từng ngày.
        </p>

        <!-- Stats strip -->
        <div class="flex flex-wrap gap-5">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-400 leading-none">Câu dịch</p>
              <p class="text-sm font-bold text-gray-900">133+ câu</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-400 leading-none">Cấp độ</p>
              <p class="text-sm font-bold text-gray-900">5 bước</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/>
              </svg>
            </div>
            <div>
              <p class="text-xs text-gray-400 leading-none">Mục tiêu</p>
              <p class="text-sm font-bold text-gray-900">Band 8.0+</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading skeletons -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-24 rounded-2xl bg-gray-200 animate-pulse"></div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="flex flex-col items-center gap-4 py-16 text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p class="text-sm">{{ error }}</p>
        <button @click="load" class="px-4 py-2 rounded-lg border border-gray-200 text-sm font-semibold text-gray-700 hover:border-[#34d399] hover:text-[#059669] transition-colors">
          Thử lại
        </button>
      </div>

      <!-- Step cards -->
      <div v-else class="space-y-3">
        <article
          v-for="step in steps"
          :key="step.id"
          class="relative flex items-center gap-4 p-5 rounded-2xl border-2 border-gray-100 bg-white cursor-pointer transition-all duration-200 hover:shadow-md hover:border-[#34d399] hover:-translate-y-0.5 group"
          @click="goToStep(step.id)"
        >
          <!-- Green left accent -->
          <div class="absolute left-0 top-4 bottom-4 w-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" style="background:#34d399"></div>

          <!-- Step icon -->
          <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center ml-2 group-hover:bg-emerald-50 transition-colors">
            <component :is="'svg'" v-bind="stepIconAttrs(step.order)" class="w-6 h-6" />
          </div>

          <!-- Text -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <span class="text-xs font-bold tracking-wider uppercase" style="color:#059669">Bước {{ step.order }}</span>
              <span v-if="step.badge_label" class="text-xs font-bold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                {{ step.badge_label }}
              </span>
            </div>
            <h3 class="text-base font-bold text-gray-900 mb-0.5 truncate">{{ step.title }}</h3>
            <p class="text-sm text-gray-500 line-clamp-1">{{ step.description }}</p>
          </div>

          <!-- Count + arrow -->
          <div class="flex-shrink-0 flex flex-col items-end gap-1">
            <span class="text-xs font-semibold text-gray-400">{{ step.sentence_count }} câu</span>
            <svg class="text-gray-300 group-hover:text-[#34d399] group-hover:translate-x-1 transition-all" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 5l7 7-7 7"/>
            </svg>
          </div>
        </article>
      </div>

      <!-- Motivating footer -->
      <div v-if="!loading && steps.length" class="mt-10 p-5 rounded-2xl bg-gradient-to-br from-gray-900 to-emerald-900 text-white text-center">
        <p class="text-sm font-medium opacity-80 mb-1">Mẹo học hiệu quả</p>
        <p class="text-base font-bold">"Mỗi ngày 10 câu dịch — sau 2 tuần bạn sẽ ngạc nhiên với chính mình." 🎯</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { fetchSteps } from '@/services/translationService.js'

const router = useRouter()
const steps  = ref([])
const loading = ref(true)
const error   = ref(null)

async function load() {
  loading.value = true
  error.value   = null
  try {
    steps.value = await fetchSteps()
  } catch {
    error.value = 'Không thể tải dữ liệu.'
  } finally {
    loading.value = false
  }
}

function goToStep(id) { router.push(`/writing/translation/${id}`) }

// ── Step icons (stroke SVG paths) ────────────────────────────────────────────
const ICON_COLORS = ['#34d399', '#34d399', '#34d399', '#34d399', '#34d399']
const ICON_PATHS = [
  // Step 1 – pencil
  ['M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7', 'M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z'],
  // Step 2 – book
  ['M4 19.5A2.5 2.5 0 016.5 17H20', 'M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z'],
  // Step 3 – target
  ['M22 12h-4', 'M6 12H2', 'M12 6V2', 'M12 22v-4', 'M12 12m-3 0a3 3 0 106 0 3 3 0 00-6 0'],
  // Step 4 – trophy
  ['M8 21h8', 'M12 17v4', 'M7 4H4a1 1 0 00-1 1v2a4 4 0 004 4h1', 'M17 4h3a1 1 0 011 1v2a4 4 0 01-4 4h-1', 'M12 17a5 5 0 005-5V4H7v8a5 5 0 005 5z'],
  // Step 5 – star/crown
  ['M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'],
]

function stepIconAttrs(order) {
  const idx   = (order - 1) % ICON_PATHS.length
  const color = ICON_COLORS[idx]
  const paths = ICON_PATHS[idx]
  return {
    xmlns: 'http://www.w3.org/2000/svg',
    fill: 'none',
    viewBox: '0 0 24 24',
    stroke: color,
    'stroke-width': '2',
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    innerHTML: paths.map(d => `<path d="${d}"/>`).join(''),
  }
}

onMounted(load)
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

<template>
  <div class="hub-page">
    <section class="section-compact">
      <div class="app-container translation-hub">
        <div class="spotify-panel">
          <div class="spotify-panel__header text-center">
            <div class="mb-3 inline-flex items-center gap-2 rounded-full border border-[var(--spotify-green)] bg-[var(--green-bg)] px-3 py-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="var(--spotify-green)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/>
              </svg>
              <span class="text-[var(--text-small)] font-bold uppercase tracking-widest text-[var(--spotify-green)]">Translation Hub</span>
            </div>
            <h1 class="font-display">
              Tập Dịch <span class="text-[var(--cta-accent)]">IELTS</span>
            </h1>
            <p class="page-subtitle mx-auto max-w-xl">
              Từ câu đơn cơ bản đến essay Band 8.0+ — lộ trình được thiết kế để bạn tiến bộ rõ ràng từng ngày.
            </p>
            <div class="mt-4 flex flex-wrap justify-center gap-5">
              <div class="stat-pill-inline">
                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--green-bg)]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="var(--spotify-green)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                  </svg>
                </div>
                <div>
                  <p class="text-[var(--text-small)] leading-none text-[var(--text-subdued)]">Câu dịch</p>
                  <p class="text-[var(--text-caption)] font-bold text-[var(--text-base)]">133+ câu</p>
                </div>
              </div>
              <div class="stat-pill-inline">
                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--green-bg)]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="var(--spotify-green)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/>
                  </svg>
                </div>
                <div>
                  <p class="text-[var(--text-small)] leading-none text-[var(--text-subdued)]">Cấp độ</p>
                  <p class="text-[var(--text-caption)] font-bold text-[var(--text-base)]">5 bước</p>
                </div>
              </div>
              <div class="stat-pill-inline">
                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--amber-bg)]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="var(--amber)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/>
                  </svg>
                </div>
                <div>
                  <p class="text-[var(--text-small)] leading-none text-[var(--text-subdued)]">Mục tiêu</p>
                  <p class="text-[var(--text-caption)] font-bold text-[var(--text-base)]">Band 8.0+</p>
                </div>
              </div>
            </div>
          </div>

          <div class="spotify-panel__body">
            <div v-if="loading" class="space-y-3">
              <div v-for="i in 5" :key="i" class="h-24 animate-pulse rounded-2xl bg-[var(--bg-interactive)]" />
            </div>

            <div v-else-if="error" class="flex flex-col items-center gap-4 py-10 text-[var(--ink3)]">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <p class="text-[var(--text-caption)]">{{ error }}</p>
              <button type="button" class="ct-btn" @click="load">Thử lại</button>
            </div>

            <div v-else class="space-y-3">
              <article
                v-for="step in steps"
                :key="step.id"
                class="group relative ml-0 flex cursor-pointer items-center gap-4 rounded-2xl border-2 border-[var(--border)] bg-[var(--bg-surface)] p-5 transition-[border-color,box-shadow,transform] duration-200 ease-in-out hover:-translate-y-0.5 hover:border-[var(--spotify-green)] hover:shadow-[var(--shadow-medium)]"
                @click="goToStep(step.id)"
              >
                <div class="absolute bottom-4 left-0 top-4 w-1 rounded-full bg-[var(--spotify-green)] opacity-0 transition-opacity duration-200 ease-in-out group-hover:opacity-100" />

                <div class="ml-2 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--bg-interactive)] transition-colors duration-200 ease-in-out group-hover:bg-[var(--green-bg)]">
                  <component :is="'svg'" v-bind="stepIconAttrs(step.order)" class="h-6 w-6" />
                </div>

                <div class="min-w-0 flex-1">
                  <div class="mb-0.5 flex items-center gap-2">
                    <span class="text-[var(--text-small)] font-bold uppercase tracking-wider text-[var(--spotify-green)]">Bước {{ step.order }}</span>
                    <span v-if="step.badge_label" class="rounded-full bg-[var(--bg-interactive)] px-2 py-0.5 text-[var(--text-small)] font-bold text-[var(--ink2)]">
                      {{ step.badge_label }}
                    </span>
                  </div>
                  <h3 class="mb-0.5 truncate text-[var(--text-body)] font-bold text-[var(--ink)]">{{ step.title }}</h3>
                  <p class="line-clamp-1 text-[var(--text-caption)] text-[var(--ink2)]">{{ step.description }}</p>
                </div>

                <div class="flex flex-shrink-0 flex-col items-end gap-1">
                  <span class="text-[var(--text-small)] font-semibold text-[var(--ink3)]">{{ step.sentence_count }} câu</span>
                  <svg class="text-[var(--ink3)] transition-[color,transform] duration-200 ease-in-out group-hover:translate-x-1 group-hover:text-[var(--spotify-green)]" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>
    <AiKeyRequiredModal :open="showGate" @close="goBack" @profile="goToProfile" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchSteps } from '@/services/translationService.js'
import { useAiKeyGate } from '@/composables/useAiKeyGate.js'
import AiKeyRequiredModal from '@/components/ui/AiKeyRequiredModal.vue'

const router = useRouter()
const { showGate, checkAiKey, goToProfile, goBack } = useAiKeyGate()
const steps = ref([])
const loading = ref(true)
const error = ref(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    steps.value = await fetchSteps()
  } catch {
    error.value = 'Không thể tải dữ liệu.'
  } finally {
    loading.value = false
  }
}

async function goToStep(id) {
  const ok = await checkAiKey()
  if (!ok) return
  router.push(`/writing/translation/steps/${id}`)
}

const ICON_PATHS = [
  ['M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7', 'M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z'],
  ['M4 19.5A2.5 2.5 0 016.5 17H20', 'M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z'],
  ['M22 12h-4', 'M6 12H2', 'M12 6V2', 'M12 22v-4', 'M12 12m-3 0a3 3 0 106 0 3 3 0 00-6 0'],
  ['M8 21h8', 'M12 17v4', 'M7 4H4a1 1 0 00-1 1v2a4 4 0 004 4h1', 'M17 4h3a1 1 0 011 1v2a4 4 0 01-4 4h-1', 'M12 17a5 5 0 005-5V4H7v8a5 5 0 005 5z'],
  ['M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'],
]

function stepIconAttrs(order) {
  const idx = (order - 1) % ICON_PATHS.length
  const paths = ICON_PATHS[idx]
  return {
    xmlns: 'http://www.w3.org/2000/svg',
    fill: 'none',
    viewBox: '0 0 24 24',
    stroke: 'var(--spotify-green)',
    'stroke-width': '2',
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    innerHTML: paths.map(d => `<path d="${d}"/>`).join(''),
  }
}

onMounted(async () => {
  await checkAiKey()
  await load()
})
</script>

<style scoped>
.translation-hub {
  max-width: 720px;
  margin: 0 auto;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

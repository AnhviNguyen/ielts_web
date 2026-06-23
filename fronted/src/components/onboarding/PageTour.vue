<template>
  <Teleport to="body">
    <Transition name="page-tour-fade">
      <div
        v-if="store.visible && currentStep"
        class="page-tour-root fixed inset-0 z-[165]"
        role="dialog"
        aria-modal="true"
        :aria-label="currentStep.title"
      >
        <div class="absolute inset-0" @click="onSkip" />

        <div
          v-if="highlight"
          class="page-tour-spotlight pointer-events-none absolute rounded-xl border-2 border-[var(--spotify-green)] transition-all duration-300 ease-out"
          :style="spotlightStyle"
        />

        <div
          ref="tooltipRef"
          class="page-tour-tooltip absolute z-[116] w-[min(340px,calc(100vw-24px))] rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4 shadow-2xl transition-all duration-300"
          :style="tooltipStyle"
        >
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-[var(--spotify-green-dark)]">
            {{ store.manualOpen ? 'Hướng dẫn' : 'Hướng dẫn lần đầu' }}
            · {{ store.stepIndex + 1 }}/{{ store.totalSteps }}
          </div>
          <h3 class="text-[15px] font-bold text-[var(--ink)]">{{ currentStep.title }}</h3>
          <p class="mt-1.5 text-[13px] leading-relaxed text-[var(--ink3)]">{{ currentStep.description }}</p>

          <div class="mt-4 flex items-center justify-between gap-2">
            <button
              type="button"
              class="text-[12px] font-medium text-[var(--ink3)] hover:text-[var(--ink)]"
              @click="onSkip"
            >
              Bỏ qua
            </button>
            <div class="flex gap-2">
              <button
                v-if="store.stepIndex > 0"
                type="button"
                class="rounded-full border border-[var(--border)] px-3.5 py-1.5 text-[12px] font-semibold text-[var(--ink2)] hover:bg-[var(--bg-interactive)]"
                @click="store.prevStep()"
              >
                Quay lại
              </button>
              <button
                type="button"
                class="rounded-full bg-[var(--spotify-green)] px-4 py-1.5 text-[12px] font-bold text-black hover:opacity-90"
                @click="onNext"
              >
                {{ store.stepIndex >= store.totalSteps - 1 ? 'Hoàn thành' : 'Tiếp theo' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import { usePageGuideStore } from '@/stores/pageGuide.js'
import { useUiStore } from '@/stores/ui.js'
import { computeTooltipPosition, padRect, waitForElement } from '@/utils/pageTourDom.js'

const store = usePageGuideStore()
const auth = useAuthStore()
const ui = useUiStore()

const highlight = ref(null)
const tooltipRef = ref(null)
const tooltipPos = ref({ top: 80, left: 16 })

const currentStep = computed(() => store.currentStep)

const spotlightStyle = computed(() => {
  if (!highlight.value) return { opacity: 0 }
  const h = highlight.value
  return {
    top: `${h.top}px`,
    left: `${h.left}px`,
    width: `${h.width}px`,
    height: `${h.height}px`,
    boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.55)',
    background: 'transparent',
  }
})

const tooltipStyle = computed(() => ({
  top: `${tooltipPos.value.top}px`,
  left: `${tooltipPos.value.left}px`,
}))

function userScope() {
  return auth.profile?.id ?? auth.profile?.email ?? 'anonymous'
}

async function refreshPosition() {
  const step = currentStep.value
  if (!step?.target) return

  if (step.target.includes('sidebar-nav') && !ui.isLargeScreen) {
    ui.openMobileSidebar()
    await new Promise((r) => setTimeout(r, 220))
  }

  const el = await waitForElement(step.target)
  if (!el || !store.visible) return

  el.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' })
  await new Promise((r) => setTimeout(r, 280))

  const raw = el.getBoundingClientRect()
  if (raw.width < 2 && raw.height < 2) {
    if (store.stepIndex < store.totalSteps - 1) store.nextStep()
    else store.finish(userScope())
    return
  }

  highlight.value = padRect(raw, 8)

  await nextTick()
  const tw = tooltipRef.value?.offsetWidth ?? 320
  const th = tooltipRef.value?.offsetHeight ?? 160
  tooltipPos.value = computeTooltipPosition(highlight.value, tw, th, step.side || 'bottom')
}

function onSkip() {
  ui.closeMobileSidebar()
  store.finish(userScope())
}

function onNext() {
  if (store.stepIndex >= store.totalSteps - 1) {
    ui.closeMobileSidebar()
    store.finish(userScope())
  } else {
    store.nextStep()
  }
}

let repositionTimer = null
function scheduleRefresh() {
  clearTimeout(repositionTimer)
  repositionTimer = setTimeout(() => refreshPosition(), 80)
}

watch(
  () => [store.visible, store.stepIndex, store.activeKey],
  ([visible]) => {
    if (visible) scheduleRefresh()
    else highlight.value = null
  },
  { immediate: true },
)

function onViewportChange() {
  if (store.visible) scheduleRefresh()
}

window.addEventListener('resize', onViewportChange)
window.addEventListener('scroll', onViewportChange, true)

onUnmounted(() => {
  window.removeEventListener('resize', onViewportChange)
  window.removeEventListener('scroll', onViewportChange, true)
  clearTimeout(repositionTimer)
})
</script>

<style scoped>
.page-tour-spotlight {
  z-index: 166;
}

.page-tour-tooltip {
  z-index: 167;
}

.page-tour-fade-enter-active,
.page-tour-fade-leave-active {
  transition: opacity 0.2s ease;
}
.page-tour-fade-enter-from,
.page-tour-fade-leave-to {
  opacity: 0;
}
</style>

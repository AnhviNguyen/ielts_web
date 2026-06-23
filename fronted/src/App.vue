<template>
  <div v-if="isAuthenticated" class="flex min-h-screen bg-[var(--bg-base)]">
    <!-- Sidebar: ẩn hoàn toàn khi ở trang quiz -->
    <AppSidebar v-if="!isQuizRoute && !isStudioRoute" />

    <div
      class="app-main flex min-h-screen min-w-0 flex-1 flex-col transition-all duration-200"
      :class="shellMainClasses"
    >
      <!-- Topbar: ẩn khi ở quiz / studio luyện tập -->
      <AppTopbar v-if="!isQuizRoute && !isStudioRoute" />
      <div
        :class="[
          isQuizRoute || isStudioRoute ? 'min-w-0 flex-1' : 'app-main__content min-w-0 flex-1 p-4 md:p-6',
          isStudioRoute ? 'bg-[var(--bg-base)]' : 'bg-[var(--bg-base)]',
        ]"
      >
        <PageBackLink v-if="showPageBack" />
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="$route.fullPath" />
          </Transition>
        </RouterView>
      </div>
    </div>
  </div>

  <div v-else class="min-h-screen bg-[var(--bg-base)]">
    <RouterView />
  </div>

  <BadgeCelebration />
  <PlacementGate v-if="isAuthenticated" @completed="onPlacementCompleted" />
  <PageTour v-if="isAuthenticated" />
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { useUiStore } from '@/stores/ui.js'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopbar  from '@/components/layout/AppTopbar.vue'
import BadgeCelebration from '@/components/ui/BadgeCelebration.vue'
import PageBackLink from '@/components/ui/PageBackLink.vue'
import PlacementGate from '@/components/onboarding/PlacementGate.vue'
import PageTour from '@/components/onboarding/PageTour.vue'
import { usePlacementStore } from '@/stores/placement.js'
import { usePageGuideStore } from '@/stores/pageGuide.js'
import { resolvePageGuideKey } from '@/utils/resolvePageGuideKey.js'

const auth = useAuthStore()
const ui   = useUiStore()
const placement = usePlacementStore()
const pageGuide = usePageGuideStore()
const route = useRoute()

const isAuthenticated  = computed(() => auth.isAuthenticated)
const sidebarCollapsed = computed(() => ui.sidebarCollapsed)
const shellMainClasses = computed(() => {
  if (isQuizRoute.value || isStudioRoute.value) return []
  return [
    'app-main--with-sidebar',
    sidebarCollapsed.value ? 'app-main--collapsed' : 'app-main--expanded',
  ]
})
const isQuizRoute = computed(() =>
  route.path.startsWith('/quiz/') ||
  route.path.startsWith('/writing/editor') ||
  route.path.startsWith('/full-exam/break') ||
  route.path.startsWith('/full-exam/writing') ||
  route.path.startsWith('/review/')
)

/** Full-bleed studio — no sidebar/topbar padding */
const isStudioRoute = computed(() =>
  route.meta.studio === true ||
  route.path.startsWith('/vocabulary/practice/') ||
  /^\/shadowing\/[a-zA-Z0-9_-]{11}/.test(route.path) ||
  (route.path.startsWith('/conversation/') && Boolean(route.params.topicId))
)

const showPageBack = computed(() => {
  if (!isAuthenticated.value) return false
  if (isQuizRoute.value || isStudioRoute.value) return false
  if (route.meta.hideBack) return false
  if (route.path === '/dashboard') return false
  return true
})

onMounted(async () => {
  ui.initTheme()
  ui.initResponsive()
  if (auth.isAuthenticated && route.path !== '/auth/google/callback') {
    if (!auth.profile) await auth.fetchProfile()
    await placement.loadStatus()
    // Cập nhật streak khi user mở app
    await auth.activityPing()
  }
})

async function onPlacementCompleted() {
  placement.closeModal()
  await placement.loadStatus()
  await auth.fetchProfile()
}

watch(() => route.path, () => {
  ui.closeMobileSidebar()
})

function pageGuideUserScope() {
  return auth.profile?.id ?? auth.profile?.email ?? 'anonymous'
}

function shouldDeferPageGuide() {
  return placement.modalOpen && placement.needsPlacement
}

function schedulePageGuide() {
  pageGuide.cancelPending()
  if (!auth.isAuthenticated || shouldDeferPageGuide()) return

  const key = resolvePageGuideKey(route)
  if (!key) return

  pageGuide.tryShow(key, pageGuideUserScope())
}

watch(
  () => [route.fullPath, auth.profile?.id, placement.modalOpen, placement.needsPlacement],
  () => schedulePageGuide(),
)

watch(
  () => placement.needsPlacement,
  (needs) => {
    if (!needs) schedulePageGuide()
  },
)
</script>

<template>
  <div v-if="isAuthenticated" class="flex min-h-screen">
    <!-- Sidebar: ẩn hoàn toàn khi ở trang quiz -->
    <AppSidebar v-if="!isQuizRoute" />

    <div
      class="flex min-h-screen flex-1 flex-col transition-all duration-200"
      :style="{ marginLeft: isQuizRoute ? '0' : (sidebarCollapsed ? '64px' : '220px') }"
    >
      <!-- Topbar: ẩn khi ở quiz (quiz có header riêng) -->
      <AppTopbar v-if="!isQuizRoute" />
      <div :class="isQuizRoute ? '' : 'flex-1 p-6'">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="$route.path" />
          </Transition>
        </RouterView>
      </div>
    </div>
  </div>

  <div v-else>
    <RouterView />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { useUiStore } from '@/stores/ui.js'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopbar  from '@/components/layout/AppTopbar.vue'

const auth = useAuthStore()
const ui   = useUiStore()
const route = useRoute()

const isAuthenticated  = computed(() => auth.isAuthenticated)
const sidebarCollapsed = computed(() => ui.sidebarCollapsed)
const isQuizRoute = computed(() => route.path.startsWith('/quiz/') || route.path.startsWith('/writing/editor'))

onMounted(async () => {
  if (auth.isAuthenticated && !auth.profile) await auth.fetchProfile()
})
</script>

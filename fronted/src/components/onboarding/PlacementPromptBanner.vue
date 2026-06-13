<template>
  <button
    v-if="showBanner"
    type="button"
    class="placement-prompt"
    @click="placement.openModal()"
  >
    <span class="placement-prompt__badge">Initial IELTS band</span>
    <span class="placement-prompt__title">Thiết lập điểm xuất phát của bạn</span>
    <span class="placement-prompt__body">
      Làm bài placement hoặc nhập band IELTS hiện có để hệ thống gợi ý lộ trình phù hợp.
    </span>
    <span class="placement-prompt__cta">
      Bắt đầu
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
    </span>
  </button>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import { usePlacementStore } from '@/stores/placement.js'

const auth = useAuthStore()
const placement = usePlacementStore()

const showBanner = computed(() => auth.isAuthenticated && placement.needsPlacement)

onMounted(async () => {
  if (auth.isAuthenticated && !placement.status) {
    await placement.loadStatus()
  }
})
</script>

<style scoped>
.placement-prompt {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
  width: 100%;
  padding: 14px 18px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--green-bg);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.placement-prompt:hover {
  border-color: var(--spotify-green);
  transform: translateY(-1px);
}
.placement-prompt__badge {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--spotify-green-dark);
}
.placement-prompt__title {
  flex: 1 1 100%;
  font-size: 14px;
  font-weight: 800;
  color: var(--ink);
}
.placement-prompt__body {
  flex: 1 1 200px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--ink3);
}
.placement-prompt__cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--spotify-green);
  color: #000;
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
}
</style>

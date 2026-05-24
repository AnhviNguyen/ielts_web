<template>
  <div class="relative" ref="rootRef">
    <button
      type="button"
      class="relative flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--bg)] text-[var(--ink2)] transition-colors hover:border-[#34d399] hover:text-[var(--ink)]"
      :aria-label="`Thông báo${unread ? ` (${unread} chưa đọc)` : ''}`"
      @click.stop="togglePanel"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
      </svg>
      <span
        v-if="unread > 0"
        class="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[#ef4444] px-1 text-[9px] font-bold text-white"
      >{{ unread > 9 ? '9+' : unread }}</span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="open"
        class="absolute right-0 top-10 z-50 w-[min(100vw-2rem,360px)] overflow-hidden rounded-2xl border border-[var(--border)] bg-white shadow-xl"
      >
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <span class="text-[13px] font-semibold text-[var(--ink)]">Thông báo</span>
          <button
            v-if="unread > 0"
            type="button"
            class="text-[11px] font-semibold text-[#059669] hover:underline"
            @click="markAll"
          >Đánh dấu đã đọc</button>
        </div>

        <div v-if="store.loading" class="px-4 py-6 text-center text-[12px] text-[var(--ink3)]">Đang tải...</div>
        <div v-else-if="!store.items.length" class="px-4 py-8 text-center text-[12px] text-[var(--ink3)]">
          Chưa có thông báo
        </div>
        <ul v-else class="max-h-[320px] overflow-y-auto">
          <li
            v-for="n in store.items"
            :key="n.id"
            class="border-b border-[var(--border)] last:border-0"
          >
            <button
              type="button"
              class="flex w-full gap-3 px-4 py-3 text-left transition-colors hover:bg-[var(--bg)]"
              :class="!n.is_read ? 'bg-[#f0fdf4]/60' : ''"
              @click="openNotification(n)"
            >
              <span
                class="mt-1 h-2 w-2 shrink-0 rounded-full"
                :class="n.is_read ? 'bg-transparent' : 'bg-[#34d399]'"
              />
              <span class="min-w-0 flex-1">
                <span class="block text-[12px] font-semibold text-[var(--ink)]">{{ n.title }}</span>
                <span class="mt-0.5 block text-[11px] leading-snug text-[var(--ink3)] line-clamp-2">{{ n.body }}</span>
              </span>
            </button>
          </li>
        </ul>

        <div class="border-t border-[var(--border)] p-3">
          <button
            type="button"
            class="w-full rounded-lg border border-[var(--border)] py-2 text-[12px] font-semibold text-[var(--ink2)] hover:bg-[var(--bg)]"
            @click="showSettings = !showSettings"
          >{{ showSettings ? 'Ẩn cài đặt' : 'Cài đặt nhắc nhở' }}</button>
          <form v-if="showSettings" class="mt-3 space-y-2" @submit.prevent="saveSettings">
            <label class="flex items-center gap-2 text-[12px]">
              <input v-model="form.reminder_enabled" type="checkbox" class="rounded" />
              Bật nhắc nhở
            </label>
            <label class="block text-[11px] text-[var(--ink3)]">
              Giờ nhắc
              <input v-model="form.reminder_time" type="time" class="mt-1 w-full rounded border border-[var(--border)] px-2 py-1.5 text-[12px]" />
            </label>
            <label class="block text-[11px] text-[var(--ink3)]">
              Kênh
              <select v-model="form.channel" class="mt-1 w-full rounded border border-[var(--border)] px-2 py-1.5 text-[12px]">
                <option value="in_app">Trong app</option>
                <option value="email">Email</option>
                <option value="both">Cả hai</option>
              </select>
            </label>
            <label class="flex items-center gap-2 text-[12px]">
              <input v-model="form.email_daily_digest" type="checkbox" class="rounded" />
              Email nhắc hàng ngày
            </label>
            <label class="flex items-center gap-2 text-[12px] opacity-70">
              <input v-model="form.push_enabled" type="checkbox" class="rounded" disabled />
              Push PWA (sắp có)
            </label>
            <button type="submit" class="btn btn-primary w-full text-[12px]">Lưu</button>
            <p v-if="settingsSaved" class="text-center text-[11px] text-[#059669]">Đã lưu cài đặt</p>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications.js'

const store = useNotificationsStore()
const router = useRouter()
const open = ref(false)
const showSettings = ref(false)
const settingsSaved = ref(false)
const rootRef = ref(null)

const unread = computed(() => store.unreadCount)

const form = reactive({
  reminder_enabled: true,
  reminder_time: '09:00',
  channel: 'in_app',
  email_daily_digest: false,
  push_enabled: false,
})

function togglePanel() {
  open.value = !open.value
  if (open.value) {
    store.load()
    store.loadSettings()
  }
}

async function openNotification(n) {
  if (!n.is_read) await store.markRead(n.id)
  open.value = false
  if (n.link_path) router.push(n.link_path)
}

async function markAll() {
  await store.markAllRead()
}

async function saveSettings() {
  await store.saveSettings({
    reminder_enabled: form.reminder_enabled,
    reminder_time: form.reminder_time.length === 5 ? `${form.reminder_time}:00` : form.reminder_time,
    channel: form.channel,
    email_daily_digest: form.email_daily_digest,
    push_enabled: form.push_enabled,
  })
  settingsSaved.value = true
  setTimeout(() => { settingsSaved.value = false }, 2500)
}

watch(
  () => store.settings,
  (s) => {
    if (!s) return
    form.reminder_enabled = s.reminder_enabled
    form.reminder_time = (s.reminder_time || '09:00:00').slice(0, 5)
    form.channel = s.channel || 'in_app'
    form.email_daily_digest = s.email_daily_digest
    form.push_enabled = s.push_enabled
  },
  { immediate: true }
)

function onDocClick(e) {
  if (rootRef.value && !rootRef.value.contains(e.target)) open.value = false
}

onMounted(() => {
  store.load()
  document.addEventListener('click', onDocClick)
})
onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>

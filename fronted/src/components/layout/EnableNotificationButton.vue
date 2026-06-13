<template>
  <div class="space-y-2 rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3">
    <div class="flex items-center justify-between gap-3">
      <div class="min-w-0">
        <p class="text-[12px] font-semibold text-[var(--ink)]">Push notification</p>
        <p class="mt-0.5 text-[11px] text-[var(--ink3)]">{{ statusText }}</p>
      </div>
      <span
        class="shrink-0 rounded-md px-2 py-1 text-[10px] font-semibold"
        :class="badgeClass"
      >
        {{ badgeText }}
      </span>
    </div>

    <div class="flex gap-2">
      <button
        type="button"
        class="ct-btn flex-1 px-3 py-2 text-[12px]"
        :disabled="primaryDisabled"
        @click="handlePrimary"
      >
        <svg v-if="loading" class="mr-1.5 inline h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        {{ primaryLabel }}
      </button>
      <button
        type="button"
        class="btn btn-primary flex-1 text-[12px]"
        :disabled="!enabled || loading || testing"
        @click="handleTest"
      >
        <svg v-if="testing" class="mr-1.5 inline h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        Kiểm tra
      </button>
    </div>

    <p v-if="message" class="text-[11px]" :class="messageClass">{{ message }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import {
  getCurrentSubscription,
  isPushNotificationSupported,
  sendTestPushNotification,
  subscribeUserToPush,
  unsubscribeUserFromPush,
} from '@/services/pushNotification.js'

const emit = defineEmits(['changed'])
const auth = useAuthStore()

const loading = ref(false)
const testing = ref(false)
const supported = ref(true)
const enabled = ref(false)
const permission = ref(typeof Notification !== 'undefined' ? Notification.permission : 'default')
const message = ref('')
const messageType = ref('success')

const isAuthenticated = computed(() => auth.isAuthenticated)

const statusText = computed(() => {
  if (!supported.value) return 'Trình duyệt này chưa hỗ trợ Web Push.'
  if (!isAuthenticated.value) return 'Đăng nhập để bật thông báo.'
  if (permission.value === 'denied') return 'Bạn đã chặn quyền thông báo trong trình duyệt.'
  if (enabled.value) return 'Đã bật cho trình duyệt hiện tại.'
  return 'Chưa bật cho trình duyệt hiện tại.'
})

const badgeText = computed(() => {
  if (!supported.value) return 'Không hỗ trợ'
  if (!isAuthenticated.value) return 'Chưa đăng nhập'
  if (permission.value === 'denied') return 'Bị chặn'
  return enabled.value ? 'Đã bật' : 'Chưa bật'
})

const badgeClass = computed(() => {
  if (enabled.value) return 'bg-[#dcfce7] text-[#047857]'
  if (!supported.value || permission.value === 'denied') return 'bg-[#fee2e2] text-[#b91c1c]'
  return 'bg-[#fef3c7] text-[#92400e]'
})

const primaryLabel = computed(() => {
  if (loading.value) return 'Đang xử lý'
  return enabled.value ? 'Tắt' : 'Bật thông báo'
})

const primaryDisabled = computed(() => (
  loading.value ||
  !supported.value ||
  !isAuthenticated.value ||
  permission.value === 'denied'
))

const messageClass = computed(() => (
  messageType.value === 'error' ? 'text-[#b91c1c]' : 'text-[#047857]'
))

async function refreshState() {
  supported.value = isPushNotificationSupported()
  permission.value = typeof Notification !== 'undefined' ? Notification.permission : 'default'
  if (!supported.value || !isAuthenticated.value) {
    enabled.value = false
    return
  }
  enabled.value = !!(await getCurrentSubscription())
}

async function handlePrimary() {
  loading.value = true
  message.value = ''
  try {
    if (enabled.value) {
      await unsubscribeUserFromPush()
      enabled.value = false
      message.value = 'Đã tắt push notification.'
    } else {
      await subscribeUserToPush()
      permission.value = Notification.permission
      enabled.value = true
      message.value = 'Đã bật push notification.'
    }
    messageType.value = 'success'
    emit('changed')
  } catch (err) {
    permission.value = typeof Notification !== 'undefined' ? Notification.permission : 'default'
    messageType.value = 'error'
    message.value = err?.response?.data?.detail || err?.message || 'Không thể cập nhật push notification.'
    await refreshState()
  } finally {
    loading.value = false
  }
}

async function handleTest() {
  testing.value = true
  message.value = ''
  try {
    const data = await sendTestPushNotification()
    messageType.value = 'success'
    message.value = `Đã gửi ${data.sent || 0} thông báo kiểm tra.`
  } catch (err) {
    messageType.value = 'error'
    message.value = err?.response?.data?.detail || 'Không gửi được thông báo kiểm tra.'
  } finally {
    testing.value = false
  }
}

onMounted(refreshState)
watch(isAuthenticated, refreshState)
</script>

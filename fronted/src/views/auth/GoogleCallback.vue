<template>
  <div class="flex min-h-screen items-center justify-center bg-[var(--bg)]">
    <div class="flex flex-col items-center gap-4">
      <!-- Spinner -->
      <div class="h-12 w-12 animate-spin rounded-full border-4 border-[#34d399] border-t-transparent"></div>
      <p class="text-[14px] text-[var(--ink2)]">{{ statusText }}</p>
      <p v-if="errorMsg" class="mt-2 max-w-xs text-center text-[13px] text-red-500">{{ errorMsg }}</p>
      <router-link v-if="errorMsg" to="/login" class="mt-2 text-[13px] text-[#34d399] underline">
        Quay lại đăng nhập
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { googleRedirectUri } from '@/utils/googleAuth.js'

const EXCHANGED_KEY = 'google_oauth_exchanged_code'
const IN_PROGRESS_KEY = 'google_oauth_in_progress'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const statusText = ref('Đang xác thực với Google...')
const errorMsg = ref('')

onMounted(async () => {
  const code = typeof route.query.code === 'string' ? route.query.code : ''
  const error = route.query.error
  const errorDesc = route.query.error_description

  if (error || !code) {
    if (error === 'access_denied') {
      errorMsg.value = 'Bạn đã hủy đăng nhập Google.'
    } else if (errorDesc) {
      errorMsg.value = `Google: ${errorDesc}`
    } else {
      errorMsg.value = 'Đăng nhập Google bị hủy hoặc thất bại. Vui lòng thử lại.'
    }
    statusText.value = ''
    return
  }

  // Strip ?code= from URL immediately so refresh/back cannot reuse the code.
  if (route.query.code) {
    await router.replace({ path: '/auth/google/callback', query: {} })
  }

  if (sessionStorage.getItem(EXCHANGED_KEY) === code) {
    await router.replace('/dashboard')
    return
  }
  if (sessionStorage.getItem(IN_PROGRESS_KEY) === code) {
    return
  }
  sessionStorage.setItem(IN_PROGRESS_KEY, code)

  try {
    const redirectUri = googleRedirectUri()
    const ok = await auth.googleAuth(code, redirectUri)
    if (ok) {
      sessionStorage.setItem(EXCHANGED_KEY, code)
      await router.replace('/dashboard')
      return
    }
    statusText.value = ''
    errorMsg.value = auth.error || 'Đăng nhập Google thất bại. Vui lòng thử lại.'
  } finally {
    sessionStorage.removeItem(IN_PROGRESS_KEY)
  }
})
</script>

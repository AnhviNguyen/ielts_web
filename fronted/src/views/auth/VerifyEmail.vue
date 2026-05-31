<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-mark font-display">Lingua<span>IELTS</span></div>
        <div class="logo-sub">AI-Powered Learning Platform</div>
      </div>

      <div class="flex justify-center mb-5">
        <div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#f0fdf4] border border-[#bbf7d0]">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
        </div>
      </div>

      <h1 class="auth-title font-display text-center">Xác minh email</h1>
      <p class="auth-sub text-center">
        Chúng tôi đã gửi mã xác minh 6 chữ số đến<br>
        <strong class="text-[var(--ink)]">{{ email }}</strong>
      </p>

      <form @submit.prevent="handleVerify" class="mt-6">
        <!-- OTP input -->
        <div class="form-group">
          <label class="form-label">Mã xác minh</label>
          <input
            v-model="code"
            type="text"
            inputmode="numeric"
            maxlength="6"
            class="form-input text-center text-xl tracking-widest font-bold"
            placeholder="• • • • • •"
            required
            autocomplete="one-time-code"
            @input="onCodeInput"
          />
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <div v-if="successMsg" class="mb-3 rounded-lg bg-[#f0fdf4] border border-[#bbf7d0] px-4 py-2.5 text-[13px] text-[#15803d] text-center">
          {{ successMsg }}
        </div>

        <button type="submit" class="btn-primary" :disabled="loading || code.length !== 6">
          {{ loading ? 'Đang xác minh...' : 'Xác minh →' }}
        </button>
      </form>

      <div class="auth-footer flex-col gap-1">
        <div>
          Không nhận được mã?
          <button
            @click="handleResend"
            :disabled="resendCooldown > 0 || resending"
            class="auth-link disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ resendCooldown > 0 ? `Gửi lại (${resendCooldown}s)` : resending ? 'Đang gửi...' : 'Gửi lại' }}
          </button>
        </div>
        <div>
          <router-link to="/login" class="text-[12px] text-[var(--ink3)] hover:text-[#34d399]">
            ← Quay lại đăng nhập
          </router-link>
        </div>
      </div>
    </div>

    <!-- Decorative panel -->
    <div class="auth-deco">
      <div class="deco-content">
        <div class="deco-badge">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline;margin-right:5px"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          Bảo mật
        </div>
        <h2 class="deco-title font-display">Bảo vệ tài khoản<br>của bạn</h2>
        <div class="deco-features">
          <div v-for="f in features" :key="f" class="deco-feature">
            <span class="feature-check">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </span> {{ f }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

const email     = ref(route.query.email || '')
const code      = ref('')
const loading   = ref(false)
const resending = ref(false)
const errorMsg  = ref('')
const successMsg = ref('')
const resendCooldown = ref(0)

let cooldownTimer = null

const features = [
  'Mã xác minh hết hạn sau 15 phút',
  'Kiểm tra thư mục Spam nếu không thấy',
  'Chỉ dùng mã mới nhất được gửi',
]

function onCodeInput(e) {
  code.value = e.target.value.replace(/\D/g, '').slice(0, 6)
}

async function handleVerify() {
  if (code.value.length !== 6) return
  errorMsg.value  = ''
  successMsg.value = ''
  loading.value   = true
  try {
    const ok = await auth.verifyEmail(email.value, code.value)
    if (ok) {
      router.push('/dashboard')
    } else {
      errorMsg.value = auth.error || 'Mã xác minh không đúng.'
    }
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  if (resendCooldown.value > 0) return
  resending.value  = true
  errorMsg.value   = ''
  successMsg.value = ''
  try {
    await auth.resendVerification(email.value)
    successMsg.value = 'Mã mới đã được gửi. Vui lòng kiểm tra hộp thư.'
    startCooldown(60)
  } catch {
    errorMsg.value = 'Không gửi được mã. Vui lòng thử lại.'
  } finally {
    resending.value = false
  }
}

function startCooldown(seconds) {
  resendCooldown.value = seconds
  cooldownTimer = setInterval(() => {
    resendCooldown.value -= 1
    if (resendCooldown.value <= 0) {
      clearInterval(cooldownTimer)
      resendCooldown.value = 0
    }
  }, 1000)
}

onMounted(() => {
  if (!email.value) router.push('/login')
  startCooldown(60)
})

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})
</script>

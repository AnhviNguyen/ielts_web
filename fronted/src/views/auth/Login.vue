<template>
  <div class="auth-page">
    <AuthThemeToggle />
    <div class="auth-card">
      <!-- Logo -->
      <div class="auth-logo">
        <div class="logo-mark font-display">Lingua<span>IELTS</span></div>
        <div class="logo-sub">AI-Powered Learning Platform</div>
      </div>

      <h1 class="auth-title font-display">Chào mừng trở lại!</h1>
      <p class="auth-sub">Đăng nhập để tiếp tục hành trình luyện thi IELTS của bạn.</p>

      <!-- Google OAuth button -->
      <button type="button" class="auth-google-btn" @click="handleGoogleLogin" :disabled="auth.loading">
        <svg width="18" height="18" viewBox="0 0 48 48" fill="none">
          <path d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z" fill="#FFC107"/>
          <path d="M6.3 14.7l7 5.1C15.2 16.2 19.3 13 24 13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 16.3 2 9.7 7.4 6.3 14.7z" fill="#FF3D00"/>
          <path d="M24 46c5.5 0 10.4-1.9 14.3-5.1L31.8 35c-2.1 1.4-4.8 2.3-7.8 2.3-6 0-11.1-3.9-12.9-9.4l-6.9 5.3C7.7 41.3 15.3 46 24 46z" fill="#4CAF50"/>
          <path d="M44.5 20H24v8.5h11.8c-.9 2.9-2.8 5.3-5.2 6.9l6.5 5.1C41.3 37.5 45 31.2 45 24c0-1.3-.2-2.7-.5-4z" fill="#1976D2"/>
        </svg>
        Đăng nhập bằng Google
      </button>

      <div class="auth-divider">
        <span>hoặc</span>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label" for="login-email">Email</label>
          <input
            id="login-email"
            v-model="email"
            type="email"
            class="form-input"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="login-password">Mật khẩu</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            class="form-input"
            placeholder="••••••••"
            required
            autocomplete="current-password"
          />
        </div>

        <div class="flex justify-end">
          <router-link to="/forgot-password" class="text-[12px] text-[var(--text-subdued)] transition-colors duration-200 hover:text-[var(--spotify-green)]">
            Quên mật khẩu?
          </router-link>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="btn-primary" :disabled="auth.loading" id="login-btn">
          {{ auth.loading ? 'Đang đăng nhập...' : 'Đăng nhập →' }}
        </button>
      </form>

      <div class="auth-footer">
        Chưa có tài khoản?
        <router-link to="/register" class="auth-link">Đăng ký miễn phí</router-link>
      </div>
    </div>

    <!-- Decorative right panel -->
    <div class="auth-deco">
      <div class="deco-content">
        <div class="deco-badge">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;margin-right:5px"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
          IELTS Ready
        </div>
        <h2 class="deco-title font-display">Chinh phục band<br>điểm mục tiêu</h2>
        <div class="deco-features">
          <div v-for="f in features" :key="f" class="deco-feature">
            <span class="feature-check">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </span> {{ f }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import AuthThemeToggle from '@/components/auth/AuthThemeToggle.vue'
import { googleRedirectUri } from '@/utils/googleAuth.js'

const auth     = useAuthStore()
const router   = useRouter()
const email    = ref('')
const password = ref('')
const errorMsg = ref('')

const features = [
  'Reading với 200+ bài đọc thực chiến',
  'Listening với âm thanh chất lượng cao',
  'Writing với AI feedback chi tiết',
  'Speaking với phân tích phát âm',
  'Từ vựng học theo thuật toán FSRS',
]

async function handleLogin() {
  errorMsg.value = ''
  const result = await auth.login(email.value, password.value)
  if (result === true) {
    router.push('/dashboard')
  } else if (result === 'not_verified') {
    router.push(`/verify-email?email=${encodeURIComponent(email.value)}`)
  } else {
    errorMsg.value = auth.error || 'Đăng nhập thất bại.'
  }
}

function handleGoogleLogin() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId) {
    errorMsg.value = 'Google OAuth chưa được cấu hình.'
    return
  }
  const redirectUri = googleRedirectUri()
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: 'code',
    scope: 'openid email profile',
    access_type: 'offline',
    prompt: 'select_account',
  })
  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`
}
</script>

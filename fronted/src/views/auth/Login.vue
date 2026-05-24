<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Logo -->
      <div class="auth-logo">
        <div class="logo-mark font-display">Lingua<span>IELTS</span></div>
        <div class="logo-sub">AI-Powered Learning Platform</div>
      </div>

      <h1 class="auth-title font-display">Chào mừng trở lại!</h1>
      <p class="auth-sub">Đăng nhập để tiếp tục hành trình luyện thi IELTS của bạn.</p>

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
          <router-link to="/forgot-password" class="text-[12px] text-[var(--ink3)] hover:text-[#34d399]">
            Quên mật khẩu?
          </router-link>
        </div>

        <div v-if="auth.error" class="error-msg">{{ auth.error }}</div>

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
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
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

const auth     = useAuthStore()
const router   = useRouter()
const email    = ref('')
const password = ref('')

const features = [
  'Reading với 200+ bài đọc thực chiến',
  'Listening với âm thanh chất lượng cao',
  'Writing với AI feedback chi tiết',
  'Speaking với phân tích phát âm',
  'Từ vựng học theo thuật toán FSRS',
]

async function handleLogin() {
  const ok = await auth.login(email.value, password.value)
  if (ok) router.push('/dashboard')
}
</script>

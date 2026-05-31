<template>
  <div class="auth-page auth-register">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-mark font-display">Lingua<span>IELTS</span></div>
        <div class="logo-sub">AI-Powered Learning Platform</div>
      </div>

      <h1 class="auth-title font-display">Tạo tài khoản miễn phí</h1>
      <p class="auth-sub">Bắt đầu hành trình chinh phục IELTS của bạn ngay hôm nay.</p>

      <!-- Google OAuth -->
      <button type="button" class="google-btn" @click="handleGoogleSignup" :disabled="auth.loading">
        <svg width="18" height="18" viewBox="0 0 48 48" fill="none">
          <path d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z" fill="#FFC107"/>
          <path d="M6.3 14.7l7 5.1C15.2 16.2 19.3 13 24 13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 16.3 2 9.7 7.4 6.3 14.7z" fill="#FF3D00"/>
          <path d="M24 46c5.5 0 10.4-1.9 14.3-5.1L31.8 35c-2.1 1.4-4.8 2.3-7.8 2.3-6 0-11.1-3.9-12.9-9.4l-6.9 5.3C7.7 41.3 15.3 46 24 46z" fill="#4CAF50"/>
          <path d="M44.5 20H24v8.5h11.8c-.9 2.9-2.8 5.3-5.2 6.9l6.5 5.1C41.3 37.5 45 31.2 45 24c0-1.3-.2-2.7-.5-4z" fill="#1976D2"/>
        </svg>
        Đăng ký bằng Google
      </button>

      <div class="auth-divider">
        <span>hoặc đăng ký bằng email</span>
      </div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="form-label" for="reg-name">Họ và tên</label>
          <input
            id="reg-name"
            v-model="fullName"
            type="text"
            class="form-input"
            placeholder="Nguyễn Văn A"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="reg-email">Email</label>
          <input
            id="reg-email"
            v-model="email"
            type="email"
            class="form-input"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="reg-password">Mật khẩu</label>
          <input
            id="reg-password"
            v-model="password"
            type="password"
            class="form-input"
            placeholder="Tối thiểu 10 ký tự"
            required
            minlength="10"
            autocomplete="new-password"
          />
        </div>

        <div class="target-row">
          <div class="form-group" style="flex:1">
            <label class="form-label">Band mục tiêu</label>
            <select v-model="targetBand" class="form-input">
              <option v-for="b in bands" :key="b" :value="b">{{ b }}</option>
            </select>
          </div>
          <div class="form-group" style="flex:1">
            <label class="form-label">Ngày thi (không bắt buộc)</label>
            <input v-model="examDate" type="date" class="form-input" />
          </div>
        </div>

        <div v-if="auth.error" class="error-msg">{{ auth.error }}</div>

        <button type="submit" class="btn-primary" :disabled="auth.loading" id="register-btn">
          {{ auth.loading ? 'Đang tạo tài khoản...' : 'Bắt đầu học miễn phí →' }}
        </button>
      </form>

      <div class="auth-footer">
        Đã có tài khoản?
        <router-link to="/login" class="auth-link">Đăng nhập</router-link>
      </div>
    </div>

    <!-- Decorative panel -->
    <div class="auth-deco">
      <div class="deco-content">
        <div class="deco-badge">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline;margin-right:5px"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
          Miễn phí hoàn toàn
        </div>
        <h2 class="deco-title font-display">Luyện thi IELTS<br>thông minh hơn</h2>
        <div class="milestone-list">
          <div v-for="m in milestones" :key="m.band" class="milestone">
            <div class="milestone-band font-display">{{ m.band }}</div>
            <div class="milestone-bar">
              <div class="milestone-fill" :style="{ width: (m.band / 9 * 100) + '%' }"></div>
            </div>
            <div class="milestone-label">{{ m.label }}</div>
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
const fullName = ref('')
const email    = ref('')
const password = ref('')
const targetBand = ref(7.0)
const examDate   = ref('')

const bands = [5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9]

const milestones = [
  { band: 5.0, label: 'Cơ bản' },
  { band: 6.0, label: 'Du học' },
  { band: 6.5, label: 'Đại học' },
  { band: 7.0, label: 'Chuyên nghiệp' },
  { band: 7.5, label: 'Thạc sĩ' },
]

async function handleRegister() {
  const result = await auth.register(email.value, password.value, fullName.value)
  if (result?.needsVerification) {
    router.push(`/verify-email?email=${encodeURIComponent(result.email)}`)
  } else if (result === true) {
    router.push('/dashboard')
  }
}

function handleGoogleSignup() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId) return
  const redirectUri = `${window.location.origin}/auth/google/callback`
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

<style scoped>
.google-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: white;
  color: var(--ink);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  margin-bottom: 4px;
}
.google-btn:hover:not(:disabled) {
  border-color: #4285f4;
  box-shadow: 0 0 0 3px rgba(66,133,244,0.12);
}
.google-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0 8px;
  color: var(--ink3);
  font-size: 12px;
}
.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}
</style>

<template>
  <div class="auth-page auth-register">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-mark font-display">Lingua<span>IELTS</span></div>
        <div class="logo-sub">AI-Powered Learning Platform</div>
      </div>

      <h1 class="auth-title font-display">Tạo tài khoản miễn phí</h1>
      <p class="auth-sub">Bắt đầu hành trình chinh phục IELTS của bạn ngay hôm nay.</p>

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
            placeholder="Tối thiểu 8 ký tự"
            required
            minlength="8"
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
  const ok = await auth.register(email.value, password.value, fullName.value)
  if (ok) router.push('/dashboard')
}
</script>

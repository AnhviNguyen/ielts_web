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

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: var(--bg);
}

.auth-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px 64px;
  background: var(--surface);
}

.auth-logo { margin-bottom: 36px; }

.logo-mark {
  font-size: 24px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
}

.logo-mark span { color: var(--green-l); }

.logo-sub {
  font-size: 11px;
  color: var(--ink3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-top: 3px;
}

.auth-title { font-size: 28px; font-weight: 700; color: var(--ink); margin-bottom: 6px; }
.auth-sub { font-size: 14px; color: var(--ink3); margin-bottom: 32px; }

.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 12px; font-weight: 600; color: var(--ink2); margin-bottom: 6px; }

.form-input {
  width: 100%;
  padding: 11px 14px;
  border: 1.5px solid var(--border2);
  border-radius: var(--r-sm);
  font-size: 14px;
  font-family: inherit;
  color: var(--ink);
  background: var(--bg);
  outline: none;
  transition: border-color 0.18s;
}

.form-input:focus { border-color: var(--green-l); background: white; }

.error-msg {
  font-size: 13px;
  color: var(--rose);
  background: var(--rose-bg);
  padding: 10px 14px;
  border-radius: var(--r-sm);
  margin-bottom: 12px;
}

.btn-primary {
  width: 100%;
  padding: 12px;
  border-radius: var(--r-sm);
  background: var(--green);
  color: white;
  font-size: 15px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.18s;
  margin-top: 4px;
}

.btn-primary:hover { background: #245c42; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(45,106,79,0.3); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

.auth-footer {
  margin-top: 24px;
  font-size: 13px;
  color: var(--ink3);
  text-align: center;
}

.auth-link {
  color: var(--green);
  font-weight: 600;
  text-decoration: none;
  margin-left: 4px;
}

.auth-link:hover { text-decoration: underline; }

/* Decorative panel */
.auth-deco {
  background: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  position: relative;
  overflow: hidden;
}

.auth-deco::before {
  content: '';
  position: absolute;
  bottom: -80px; right: -60px;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(82,183,136,0.2) 0%, transparent 70%);
}

.auth-deco::after {
  content: '';
  position: absolute;
  top: -80px; left: -60px;
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(72,149,239,0.15) 0%, transparent 70%);
}

.deco-content { position: relative; z-index: 1; }

.deco-badge {
  display: inline-block;
  padding: 5px 14px;
  border-radius: 20px;
  background: rgba(82,183,136,0.2);
  color: var(--green-l);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 20px;
  border: 1px solid rgba(82,183,136,0.3);
}

.deco-title {
  font-size: 36px;
  font-weight: 700;
  color: white;
  line-height: 1.2;
  margin-bottom: 28px;
}

.deco-features { display: flex; flex-direction: column; gap: 12px; }

.deco-feature {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: rgba(255,255,255,0.7);
}

.feature-check {
  width: 20px; height: 20px;
  border-radius: 50%;
  background: var(--green-l);
  color: white;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .auth-page { grid-template-columns: 1fr; }
  .auth-deco { display: none; }
  .auth-card { padding: 40px 24px; }
}
</style>

<template>
  <div class="auth-page">
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
  padding: 48px 64px;
  background: var(--surface);
}

.auth-logo { margin-bottom: 28px; }

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

.auth-title { font-size: 26px; font-weight: 700; color: var(--ink); margin-bottom: 6px; }
.auth-sub { font-size: 13px; color: var(--ink3); margin-bottom: 28px; }

.form-group { margin-bottom: 14px; }
.form-label { display: block; font-size: 12px; font-weight: 600; color: var(--ink2); margin-bottom: 5px; }

.target-row { display: flex; gap: 12px; }

.form-input {
  width: 100%;
  padding: 10px 13px;
  border: 1.5px solid var(--border2);
  border-radius: var(--r-sm);
  font-size: 13px;
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
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.18s;
  margin-top: 4px;
}

.btn-primary:hover { background: #245c42; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

.auth-footer {
  margin-top: 20px;
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

/* Deco */
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
  bottom: -100px; right: -80px;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(82,183,136,0.2) 0%, transparent 70%);
}

.deco-content { position: relative; z-index: 1; width: 100%; }

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
  font-size: 32px;
  font-weight: 700;
  color: white;
  line-height: 1.2;
  margin-bottom: 32px;
}

.milestone-list { display: flex; flex-direction: column; gap: 14px; }

.milestone {
  display: flex;
  align-items: center;
  gap: 12px;
}

.milestone-band {
  font-size: 16px;
  font-weight: 700;
  color: var(--green-l);
  width: 36px;
  flex-shrink: 0;
}

.milestone-bar {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.1);
  border-radius: 99px;
  overflow: hidden;
}

.milestone-fill {
  height: 100%;
  background: linear-gradient(to right, var(--green-l), var(--blue-l));
  border-radius: 99px;
}

.milestone-label { font-size: 12px; color: rgba(255,255,255,0.5); width: 80px; }

@media (max-width: 768px) {
  .auth-page { grid-template-columns: 1fr; }
  .auth-deco { display: none; }
  .auth-card { padding: 40px 24px; }
}
</style>

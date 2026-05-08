<template>
  <div class="profile-page">
    <div class="profile-grid">
      <!-- Left: Info card -->
      <div class="card profile-card">
        <div class="avatar-section">
          <div class="avatar-large">{{ initials }}</div>
          <div class="avatar-info">
            <div class="user-name font-display">{{ auth.profile?.full_name || 'Người dùng' }}</div>
            <div class="user-email">{{ auth.profile?.email }}</div>
            <div class="user-level-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
              14 ngày streak · 2,840 XP
            </div>
          </div>
        </div>

        <!-- Stats row -->
        <div class="stats-row">
          <div class="stat-box">
            <div class="stat-val font-display">87</div>
            <div class="stat-label">Bài đã làm</div>
          </div>
          <div class="stat-box">
            <div class="stat-val font-display">6.5</div>
            <div class="stat-label">Band trung bình</div>
          </div>
          <div class="stat-box">
            <div class="stat-val font-display">32h</div>
            <div class="stat-label">Tổng thời gian</div>
          </div>
        </div>
      </div>

      <!-- Right: Edit form -->
      <div class="card" style="padding: 24px;">
        <div class="section-title font-display" style="margin-bottom: 20px;">Chỉnh sửa thông tin</div>

        <form @submit.prevent="saveProfile">
          <div class="form-group">
            <label class="form-label">Họ và tên</label>
            <input v-model="form.full_name" class="form-input" type="text" placeholder="Nhập họ và tên" />
          </div>
          <div class="form-group">
            <label class="form-label">Email</label>
            <input :value="auth.profile?.email" class="form-input" type="email" disabled />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Band mục tiêu</label>
              <select v-model="form.target_band" class="form-input">
                <option v-for="b in bands" :key="b" :value="b">{{ b }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Ngày thi dự kiến</label>
              <input v-model="form.exam_date" class="form-input" type="date" />
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-danger" @click="auth.logout()">Đăng xuất</button>
            <button type="submit" class="btn-primary" :disabled="auth.loading">
              {{ auth.loading ? 'Đang lưu...' : 'Lưu thay đổi' }}
            </button>
          </div>

          <div v-if="auth.error" class="error-msg">{{ auth.error }}</div>
          <div v-if="saved" class="success-msg">✅ Đã lưu thành công!</div>
        </form>
      </div>
    </div>

    <!-- Change password -->
    <div class="card" style="padding: 24px; margin-top: 20px;">
      <div class="section-title font-display" style="margin-bottom: 20px;">Đổi mật khẩu</div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Mật khẩu hiện tại</label>
          <input v-model="pwForm.current" class="form-input" type="password" placeholder="••••••••" />
        </div>
        <div class="form-group">
          <label class="form-label">Mật khẩu mới</label>
          <input v-model="pwForm.newPw" class="form-input" type="password" placeholder="••••••••" />
        </div>
        <div class="form-group">
          <label class="form-label">Xác nhận mật khẩu</label>
          <input v-model="pwForm.confirm" class="form-input" type="password" placeholder="••••••••" />
        </div>
      </div>
      <button class="btn-primary" @click="changePassword">Đổi mật khẩu</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth.js'

const auth  = useAuthStore()
const saved = ref(false)

const initials = computed(() => {
  const name = auth.profile?.full_name || 'U'
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

const bands = [5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9]

const form = ref({
  full_name:   auth.profile?.full_name || '',
  target_band: auth.profile?.target_band || 7.0,
  exam_date:   auth.profile?.exam_date || '',
})

const pwForm = ref({ current: '', newPw: '', confirm: '' })

async function saveProfile() {
  const ok = await auth.updateProfile(form.value)
  if (ok) { saved.value = true; setTimeout(() => saved.value = false, 3000) }
}

function changePassword() {
  alert('Tính năng đổi mật khẩu sẽ được tích hợp sau!')
}

onMounted(async () => {
  if (!auth.profile) await auth.fetchProfile()
  form.value.full_name = auth.profile?.full_name || ''
})
</script>

<style scoped>
.profile-page { max-width: 900px; }
.profile-grid { display: grid; grid-template-columns: 1fr 1.4fr; gap: 20px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  box-shadow: var(--shadow-sm);
}

.profile-card { padding: 28px; }

.avatar-section { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }

.avatar-large {
  width: 68px; height: 68px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--green-l), var(--blue-l));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 24px; color: white; flex-shrink: 0;
}

.user-name { font-size: 18px; font-weight: 600; color: var(--ink); }
.user-email { font-size: 13px; color: var(--ink3); margin-top: 2px; }
.user-level-badge {
  margin-top: 6px; font-size: 11px; font-weight: 600;
  color: var(--green); display: flex; align-items: center; gap: 4px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.stat-box { text-align: center; }
.stat-val { font-size: 24px; font-weight: 700; color: var(--ink); }
.stat-label { font-size: 11px; color: var(--ink3); margin-top: 2px; }

.section-title { font-size: 16px; font-weight: 600; color: var(--ink); }

.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.form-label { font-size: 12px; font-weight: 600; color: var(--ink2); }
.form-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }

.form-input {
  padding: 9px 12px;
  border: 1.5px solid var(--border2);
  border-radius: var(--r-sm);
  font-size: 13px;
  font-family: inherit;
  color: var(--ink);
  background: var(--bg);
  outline: none;
  transition: border-color 0.18s;
}

.form-input:focus { border-color: var(--green-l); }
.form-input:disabled { opacity: 0.5; cursor: not-allowed; }

.form-actions { display: flex; justify-content: space-between; margin-top: 20px; }

.btn-primary {
  padding: 9px 20px; border-radius: var(--r-sm);
  background: var(--green); color: white;
  font-size: 13px; font-weight: 600; border: none;
  cursor: pointer; font-family: inherit; transition: all 0.18s;
}
.btn-primary:hover { background: #245c42; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-danger {
  padding: 9px 20px; border-radius: var(--r-sm);
  background: transparent; color: var(--rose);
  font-size: 13px; font-weight: 600;
  border: 1px solid var(--rose-l);
  cursor: pointer; font-family: inherit; transition: all 0.18s;
}
.btn-danger:hover { background: var(--rose-bg); }

.error-msg { margin-top: 10px; font-size: 13px; color: var(--rose); }
.success-msg { margin-top: 10px; font-size: 13px; color: var(--green); }
</style>

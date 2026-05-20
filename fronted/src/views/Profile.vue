<template>
  <div class="profile-page">
    <div class="profile-grid">
      <!-- Left: Info card -->
      <div class="card profile-card">
        <div class="avatar-section">
          <!-- Avatar with upload overlay -->
          <div class="avatar-wrapper">
            <img :src="avatarSrc" :alt="initials" class="avatar-img" />
            <label class="avatar-upload-overlay" title="Đổi ảnh đại diện">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
              <input type="file" accept="image/*" class="hidden" @change="handleAvatarChange" :disabled="auth.loading" />
            </label>
          </div>
          <div class="avatar-info">
            <div class="user-name font-display">{{ auth.profile?.full_name || 'Người dùng' }}</div>
            <div class="user-email">{{ auth.profile?.email }}</div>
            <div class="user-level-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
              {{ auth.profile?.streak ?? 0 }} ngày streak · {{ (auth.profile?.xp ?? 0).toLocaleString('vi-VN') }} XP
            </div>
          </div>
        </div>

        <!-- Upload status -->
        <div v-if="avatarUploading" class="upload-status">
          <svg class="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M22 12a10 10 0 0 1-10 10"/></svg>
          Đang tải ảnh...
        </div>
        <div v-if="avatarError" class="error-msg text-[12px]">{{ avatarError }}</div>
        <div v-if="avatarSuccess" class="success-msg text-[12px]">✅ Cập nhật ảnh thành công!</div>

        <!-- Stats row -->
        <div class="stats-row">
          <div class="stat-box">
            <div class="stat-val font-display">{{ totalAttempts }}</div>
            <div class="stat-label">Bài đã làm</div>
          </div>
          <div class="stat-box">
            <div class="stat-val font-display">{{ avgBand }}</div>
            <div class="stat-label">Band trung bình</div>
          </div>
          <div class="stat-box">
            <div class="stat-val font-display">{{ totalHours }}</div>
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
            <button type="button" class="btn-danger" @click="handleLogout">Đăng xuất</button>
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
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { useIeltsStore } from '@/stores/ielts.js'

const auth   = useAuthStore()
const ielts  = useIeltsStore()
const router = useRouter()
const saved  = ref(false)

// ── Avatar ────────────────────────────────────────────────────────
const avatarSrc     = computed(() => auth.profile?.avatar_url || '/icon_profile.jpg')
const avatarUploading = ref(false)
const avatarError   = ref('')
const avatarSuccess = ref(false)

async function handleAvatarChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    avatarError.value = 'Ảnh không được vượt quá 2MB'
    return
  }
  avatarError.value = ''
  avatarUploading.value = true
  const ok = await auth.uploadAvatar(file)
  avatarUploading.value = false
  if (ok) {
    avatarSuccess.value = true
    setTimeout(() => { avatarSuccess.value = false }, 3000)
  } else {
    avatarError.value = auth.error || 'Upload thất bại'
  }
}

// ── Initials (fallback) ───────────────────────────────────────────
const initials = computed(() => {
  const name = auth.profile?.full_name || 'U'
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

// ── Stats from real API data ──────────────────────────────────────
const totalAttempts = computed(() => ielts.history.length || 0)
const avgBand = computed(() => {
  const bands = Object.values(ielts.bandScores).filter(Boolean)
  if (!bands.length) return '—'
  return (bands.reduce((a, b) => a + b, 0) / bands.length).toFixed(1)
})
const totalHours = computed(() => {
  const totalSec = ielts.history.reduce((acc, h) => {
    const dur = parseInt(h.duration) || 0
    return acc + dur
  }, 0)
  if (totalSec < 60) return '0h'
  return `${Math.round(totalSec / 3600)}h`
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

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(async () => {
  if (!auth.profile) await auth.fetchProfile()
  form.value.full_name = auth.profile?.full_name || ''
  form.value.target_band = auth.profile?.target_band || 7.0
  form.value.exam_date = auth.profile?.exam_date || ''
  if (!ielts.history.length) await ielts.fetchHistory()
  if (!ielts.bandScores.reading) await ielts.fetchStats()
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

.avatar-section { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }

.avatar-wrapper {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  flex-shrink: 0;
}

.avatar-img {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.avatar-upload-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  cursor: pointer;
  transition: opacity 0.18s;
}

.avatar-wrapper:hover .avatar-upload-overlay {
  opacity: 1;
}

.upload-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ink3);
  margin-bottom: 8px;
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
  margin-top: 16px;
}

.stat-box { text-align: center; }
.stat-val { font-size: 24px; font-weight: 700; color: var(--ink); }
.stat-label { font-size: 11px; color: var(--ink3); margin-top: 2px; }

.section-title { font-size: 16px; font-weight: 600; color: var(--ink); }

.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.form-label { font-size: 12px; font-weight: 600; color: var(--ink2); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

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

.avatar-info { flex: 1; min-width: 0; }
</style>

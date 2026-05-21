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

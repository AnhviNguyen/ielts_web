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
          <AppLoading :size="32" message="Đang tải ảnh..." inline />
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

    <!-- Badges -->
    <div class="card badges-section">
      <div class="badges-header">
        <div>
          <div class="section-title font-display">Huy hiệu</div>
          <p class="badges-subtitle">Mở khóa bằng cách luyện Reading, Listening, Writing, Speaking và từ vựng.</p>
        </div>
        <div class="badges-progress-wrap">
          <div class="badges-progress-label">
            <span>{{ badgesUnlocked }}/{{ badgesTotal }}</span>
            <span class="text-[var(--ink3)]">đã mở</span>
          </div>
          <div class="badges-progress-bar">
            <div
              class="badges-progress-fill"
              :style="{ width: badgeProgressPct + '%' }"
            />
          </div>
        </div>
      </div>

      <div class="badges-filters">
        <button
          type="button"
          class="badges-filter-btn"
          :class="{ active: badgeFilter === 'all' }"
          @click="badgeFilter = 'all'"
        >Tất cả</button>
        <button
          type="button"
          class="badges-filter-btn"
          :class="{ active: badgeFilter === 'unlocked' }"
          @click="badgeFilter = 'unlocked'"
        >Đã mở ({{ badgesUnlocked }})</button>
        <button
          type="button"
          class="badges-filter-btn"
          :class="{ active: badgeFilter === 'locked' }"
          @click="badgeFilter = 'locked'"
        >Chưa mở ({{ badgesTotal - badgesUnlocked }})</button>
      </div>

      <AppLoading v-if="badgesLoading" :size="40" message="Đang tải huy hiệu..." />
      <div v-else class="badges-grid">
        <button
          v-for="b in filteredBadges"
          :key="b.id"
          type="button"
          class="badge-card"
          :class="b.unlocked ? 'badge-card--unlocked' : 'badge-card--locked'"
          @click="openBadgeHint(b)"
          @mouseenter="onBadgeHover(b)"
        >
          <div class="badge-card-icon" :class="b.unlocked ? 'text-[#059669]' : 'text-[var(--ink3)]'">
            <BadgeIcon :name="b.icon" :size="28" />
          </div>
          <div class="badge-card-body">
            <div class="badge-card-title">{{ b.title }}</div>
            <div class="badge-card-desc">{{ b.description }}</div>
          </div>
          <span v-if="b.unlocked" class="badge-card-check" aria-label="Đã mở khóa">✓</span>
          <svg v-else class="badge-card-lock" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        </button>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="badge-celebrate">
        <div
          v-if="badgeHint"
          class="badge-hint-overlay"
          role="dialog"
          aria-modal="true"
          @click.self="badgeHint = null"
        >
          <div class="badge-hint-popover">
            <div class="badge-hint-icon" :class="badgeHint.unlocked ? 'text-[#059669]' : 'text-[var(--ink3)]'">
              <BadgeIcon :name="badgeHint.icon" :size="40" />
            </div>
            <h3 class="badge-hint-title font-display">{{ badgeHint.title }}</h3>
            <p class="badge-hint-desc">{{ badgeHint.description }}</p>
            <div class="badge-hint-box">
              <span class="badge-hint-label">Cách nhận huy hiệu</span>
              <p>{{ badgeHint.hint || badgeHint.description }}</p>
            </div>
            <p v-if="badgeHint.unlocked" class="badge-hint-status badge-hint-status--done">✓ Bạn đã mở khóa huy hiệu này</p>
            <p v-else class="badge-hint-status">Tiếp tục luyện tập để mở khóa!</p>
            <button type="button" class="btn btn-primary w-full mt-3" @click="badgeHint = null">Đóng</button>
          </div>
        </div>
      </Transition>
    </Teleport>

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
      <button class="btn-primary" :disabled="auth.loading" @click="changePassword">
        {{ auth.loading ? 'Đang xử lý...' : 'Đổi mật khẩu' }}
      </button>
      <div v-if="pwError" class="error-msg" style="margin-top: 12px;">{{ pwError }}</div>
      <div v-if="pwSuccess" class="success-msg" style="margin-top: 12px;">✅ Đã đổi mật khẩu!</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client.js'
import { useAuthStore } from '@/stores/auth.js'
import { useIeltsStore } from '@/stores/ielts.js'
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'
import AppLoading from '@/components/ui/AppLoading.vue'
import BadgeIcon from '@/components/ui/BadgeIcon.vue'

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
const pwError = ref('')
const pwSuccess = ref(false)

const badges = ref([])
const badgesLoading = ref(false)
const badgesUnlocked = ref(0)
const badgesTotal = ref(0)
const badgeFilter = ref('all')
const badgeCelebration = useBadgeCelebrationStore()
const badgeHint = ref(null)
let hoverTimer = null

function openBadgeHint(b) {
  badgeHint.value = b
}

function onBadgeHover(b) {
  if (hoverTimer) clearTimeout(hoverTimer)
  hoverTimer = setTimeout(() => {
    badgeHint.value = b
  }, 600)
}

const badgeProgressPct = computed(() => {
  if (!badgesTotal.value) return 0
  return Math.round((badgesUnlocked.value / badgesTotal.value) * 100)
})

const filteredBadges = computed(() => {
  if (badgeFilter.value === 'unlocked') return badges.value.filter(b => b.unlocked)
  if (badgeFilter.value === 'locked') return badges.value.filter(b => !b.unlocked)
  return badges.value
})

async function loadBadges() {
  badgesLoading.value = true
  try {
    const { data } = await apiClient.get('/users/me/badges')
    badges.value = data.items || []
    badgesUnlocked.value = data.unlocked_count ?? 0
    badgesTotal.value = data.total_count ?? badges.value.length
    badgeCelebration.syncKnownFromBadges(badges.value)
  } catch {
    badges.value = []
  } finally {
    badgesLoading.value = false
  }
}

async function saveProfile() {
  const ok = await auth.updateProfile(form.value)
  if (ok) { saved.value = true; setTimeout(() => saved.value = false, 3000) }
}

async function changePassword() {
  pwError.value = ''
  pwSuccess.value = false
  if (!pwForm.value.current || !pwForm.value.newPw) {
    pwError.value = 'Vui lòng nhập đủ mật khẩu.'
    return
  }
  if (pwForm.value.newPw.length < 6) {
    pwError.value = 'Mật khẩu mới tối thiểu 6 ký tự.'
    return
  }
  if (pwForm.value.newPw !== pwForm.value.confirm) {
    pwError.value = 'Xác nhận mật khẩu không khớp.'
    return
  }
  const ok = await auth.changePassword(pwForm.value.current, pwForm.value.newPw)
  if (ok) {
    pwSuccess.value = true
    pwForm.value = { current: '', newPw: '', confirm: '' }
    setTimeout(() => { pwSuccess.value = false }, 4000)
  } else {
    pwError.value = auth.error || 'Đổi mật khẩu thất bại'
  }
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
  await loadBadges()
})
</script>

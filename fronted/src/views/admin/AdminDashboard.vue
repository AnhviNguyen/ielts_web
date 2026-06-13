<template>
  <div class="admin-page mx-auto max-w-7xl space-y-6" :style="pageStyle">
    <AdminPageHeader
      module="dashboard"
      title="Bảng điều khiển quản trị"
      subtitle="Theo dõi người dùng, hoạt động luyện tập, phân bố điểm band và tín hiệu bất thường trên nền tảng LinguaIELTS."
    >
      <template #actions>
        <div class="flex flex-wrap gap-2">
          <RouterLink to="/admin/users" class="ct-btn ct-btn-accent">Quản lý người dùng</RouterLink>
          <RouterLink to="/admin/leaderboard" class="ct-btn">Quản trị BXH</RouterLink>
        </div>
      </template>
    </AdminPageHeader>

    <div v-if="loading" class="rounded-xl border border-[var(--border)] bg-white p-8 text-center text-sm text-[var(--ink3)]">
      Đang tải dữ liệu thống kê...
    </div>
    <div v-else-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>

    <template v-else-if="overview">
      <!-- KPI cards -->
      <section class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        <AdminStatCard
          v-for="card in statCards"
          :key="card.label"
          :label="card.label"
          :value="card.value"
          :hint="card.hint"
          :icon="card.icon"
          :color="card.color"
          :accent="card.accent"
          :trend="card.trend"
          :class="card.span"
        />
      </section>

      <!-- Quick actions — một dòng, stroke icons -->
      <AdminPanel title="Truy cập nhanh" subtitle="Quản lý người dùng và nội dung CMS" accent module="dashboard">
        <AdminQuickLinks :links="quickLinks" />
      </AdminPanel>

      <!-- Activity charts -->
      <section class="grid gap-4 lg:grid-cols-3">
        <AdminPanel class="lg:col-span-2" title="Hoạt động 7 ngày" subtitle="Bài làm và người dùng hoạt động (DAU)" accent module="dashboard">
          <AdminLineChart :labels="chartLabels" :series="activitySeries" :height="220" />
        </AdminPanel>
        <AdminPanel title="Đăng ký mới" subtitle="Tài khoản tạo trong 7 ngày">
          <AdminBarChart :items="signupBars" color="#60a5fa" suffix=" user" />
        </AdminPanel>
      </section>

      <!-- Skills & bands -->
      <section class="grid gap-4 lg:grid-cols-3">
        <AdminPanel title="Band trung bình theo kỹ năng" subtitle="Từ lịch sử làm bài">
          <AdminBarChart
            :items="skillBars"
            :color="'#059669'"
            suffix=" lần"
          />
        </AdminPanel>
        <AdminPanel title="Phân bố band" subtitle="Số lượt theo mức điểm">
          <AdminDonutChart :items="bandDonut" />
        </AdminPanel>
        <AdminPanel title="Lượt làm theo kỹ năng" subtitle="Tổng attempts theo subject">
          <AdminBarChart :items="subjectBars" color="#8b5cf6" />
        </AdminPanel>
      </section>

      <!-- Streak & retention -->
      <section class="grid gap-4 lg:grid-cols-2">
        <AdminPanel title="Phân bố streak" subtitle="Số ngày học liên tiếp">
          <div class="grid grid-cols-4 gap-3">
            <div
              v-for="(bucket, i) in overview.streak_buckets"
              :key="bucket.label"
              class="rounded-xl p-4 text-center"
              :style="{ backgroundColor: streakColors[i] + '18' }"
            >
              <div class="text-2xl font-bold" :style="{ color: streakColors[i] }">{{ bucket.count }}</div>
              <div class="mt-1 text-xs font-semibold text-[var(--ink3)]">{{ bucket.label }} ngày</div>
            </div>
          </div>
        </AdminPanel>
        <AdminPanel title="Giữ chân theo streak" subtitle="Tỷ lệ hoạt động 7 ngày gần nhất">
          <div class="space-y-3">
            <div v-for="bucket in overview.retention_by_streak" :key="bucket.label" class="rounded-lg bg-[var(--bg)] p-3">
              <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-[var(--ink)]">Streak {{ bucket.label }} ngày</span>
                <span class="text-[var(--ink3)]">{{ bucket.active_last_7_days }}/{{ bucket.total_users }} user</span>
              </div>
              <div class="mt-2 h-2.5 overflow-hidden rounded-full bg-white">
                <div
                  class="h-full rounded-full bg-gradient-to-r from-amber-400 to-orange-500 transition-all"
                  :style="{ width: `${Math.max(4, bucket.retention_rate)}%` }"
                />
              </div>
              <div class="mt-1 text-[10px] text-[var(--ink3)]">
                Hôm nay {{ bucket.active_today }} · {{ bucket.retention_rate }}% retention
              </div>
            </div>
          </div>
        </AdminPanel>
      </section>

      <!-- Heatmap + Suspicious signals — side by side -->
      <section class="grid gap-4 lg:grid-cols-2">
        <AdminPanel
          class="min-w-0"
          title="Bản đồ hoạt động"
          subtitle="Số bài làm mỗi ngày — 12 tuần gần nhất (GitHub-style)"
        >
          <AdminHeatmap :days="overview.activity_heatmap || []" />
        </AdminPanel>

        <AdminPanel class="min-w-0" :padded="false" title="Tín hiệu đáng ngờ" subtitle="XP cao bất thường, streak dài, nhiều bài trong 24h, nhảy band đột ngột">
          <template #action>
            <RouterLink to="/admin/leaderboard" class="text-xs font-semibold text-emerald-600 hover:underline">
              Mở quản trị BXH →
            </RouterLink>
          </template>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
                <tr>
                  <th class="px-3 py-2.5">Người dùng</th>
                  <th class="px-3 py-2.5">XP</th>
                  <th class="px-3 py-2.5">Streak</th>
                  <th class="px-3 py-2.5">24h</th>
                  <th class="px-3 py-2.5">Lý do</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="user in overview.top_suspicious_users"
                  :key="user.id"
                  class="border-t border-[var(--border)] transition-colors hover:bg-emerald-50/30"
                >
                  <td class="px-3 py-3">
                    <RouterLink :to="`/admin/users/${user.id}`" class="font-semibold text-[var(--ink)] hover:text-emerald-600">
                      {{ user.full_name || user.email }}
                    </RouterLink>
                    <div class="truncate text-xs text-[var(--ink3)]">{{ user.email }}</div>
                  </td>
                  <td class="px-3 py-3 font-semibold tabular-nums">{{ user.xp }}</td>
                  <td class="px-3 py-3 tabular-nums">{{ user.streak }}</td>
                  <td class="px-3 py-3 tabular-nums">{{ user.attempts_24h }}</td>
                  <td class="px-3 py-3">
                    <div class="flex flex-wrap gap-1">
                      <span
                        v-for="reason in user.reasons"
                        :key="reason"
                        class="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700"
                      >{{ reason }}</span>
                    </div>
                  </td>
                </tr>
                <tr v-if="!overview.top_suspicious_users.length">
                  <td colspan="5" class="px-3 py-10 text-center text-sm text-[var(--ink3)]">
                    Chưa phát hiện tín hiệu bất thường.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </AdminPanel>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { adminService } from '@/services/adminService.js'
import AdminStatCard from '@/components/admin/AdminStatCard.vue'
import AdminPanel from '@/components/admin/AdminPanel.vue'
import AdminLineChart from '@/components/admin/AdminLineChart.vue'
import AdminDonutChart from '@/components/admin/AdminDonutChart.vue'
import AdminBarChart from '@/components/admin/AdminBarChart.vue'
import AdminHeatmap from '@/components/admin/AdminHeatmap.vue'
import AdminQuickLinks from '@/components/admin/AdminQuickLinks.vue'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import { ADMIN_STROKE_ICONS } from '@/components/admin/adminIcons.js'
import { ADMIN_MODULES, moduleStyle } from '@/components/admin/adminModules.js'

const pageStyle = moduleStyle('dashboard')

const ICON = {
  users: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
  active: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  lock: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  dau: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
  attempts: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
  band: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
  alert: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  total: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
}

const streakColors = ['#9ca3af', '#60a5fa', '#34d399', '#059669']

const overview = ref(null)
const loading = ref(true)
const error = ref('')

function dayTrend(series, index = -1) {
  const arr = series || []
  if (arr.length < 2) return null
  const today = Number(arr[index]?.attempts ?? arr[index]?.active_users ?? 0)
  const yesterday = Number(arr[index - 1]?.attempts ?? arr[index - 1]?.active_users ?? 0)
  if (!yesterday) return today > 0 ? 100 : 0
  return Math.round(((today - yesterday) / yesterday) * 100)
}

const statCards = computed(() => {
  const o = overview.value
  if (!o) return []
  return [
    { label: 'Tổng user', value: o.total_users, icon: ICON.users, color: '#059669', hint: `${o.active_users} đang hoạt động`, span: 'xl:col-span-2', accent: true },
    { label: 'DAU hôm nay', value: o.dau_today, icon: ICON.dau, color: '#3b82f6', trend: dayTrend(o.dau_last_7_days?.map((d) => ({ attempts: d.active_users }))), span: 'xl:col-span-2' },
    { label: 'Bài làm hôm nay', value: o.attempts_today, icon: ICON.attempts, color: '#8b5cf6', trend: dayTrend(o.attempts_last_7_days), span: 'xl:col-span-2' },
    { label: 'Tổng bài làm', value: o.total_attempts ?? 0, icon: ICON.total, color: '#6366f1', hint: 'All time', span: 'xl:col-span-2' },
    { label: 'Band TB', value: (o.overall_average_band ?? 0).toFixed(1), icon: ICON.band, color: '#f59e0b', hint: 'Trung bình toàn hệ thống', span: 'xl:col-span-2' },
    { label: 'Đã khóa', value: o.locked_users, icon: ICON.lock, color: '#ef4444', span: 'xl:col-span-2' },
    { label: 'Đáng ngờ', value: o.top_suspicious_users?.length ?? 0, icon: ICON.alert, color: '#f97316', span: 'xl:col-span-2' },
    { label: 'Active', value: o.active_users, icon: ICON.active, color: '#10b981', span: 'xl:col-span-2' },
  ]
})

const quickLinks = computed(() => {
  const c = overview.value?.content_counts || {}
  const m = ADMIN_MODULES
  return [
    { to: '/admin/users', label: 'Người dùng', icon: ADMIN_STROKE_ICONS.users, color: m.users.color },
    { to: '/admin/leaderboard', label: 'BXH', icon: ADMIN_STROKE_ICONS.leaderboard, color: m.leaderboard.color },
    { to: '/admin/system-vocab', label: 'Từ vựng', icon: ADMIN_STROKE_ICONS.vocab, color: m.vocab.color, count: c.system_vocab_topics },
    { to: '/admin/content/writing', label: 'Writing', icon: ADMIN_STROKE_ICONS.writing, color: m.writing.color },
    { to: '/admin/content/mock-tests', label: 'Reading', icon: ADMIN_STROKE_ICONS.reading, color: m.reading.color },
    { to: '/admin/content/listening', label: 'Listening', icon: ADMIN_STROKE_ICONS.listening, color: m.listening.color },
    { to: '/admin/content/speaking', label: 'Speaking', icon: ADMIN_STROKE_ICONS.speaking, color: m.speaking.color },
    { to: '/admin/content/conversation', label: 'Hội thoại', icon: ADMIN_STROKE_ICONS.conversation, color: m.conversation.color, count: c.conversation_topics },
    { to: '/admin/content/translation', label: 'Dịch', icon: ADMIN_STROKE_ICONS.translation, color: m.translation.color, count: c.translation_topics },
  ]
})

const chartLabels = computed(() =>
  (overview.value?.attempts_last_7_days || []).map((d) => formatShortDate(d.date))
)

const activitySeries = computed(() => [
  {
    label: 'Bài làm',
    color: '#059669',
    data: (overview.value?.attempts_last_7_days || []).map((d) => d.attempts),
  },
  {
    label: 'DAU',
    color: '#3b82f6',
    data: (overview.value?.dau_last_7_days || []).map((d) => d.active_users),
  },
])

const signupBars = computed(() =>
  (overview.value?.new_users_last_7_days || []).map((d) => ({
    label: formatShortDate(d.date),
    value: d.attempts,
  }))
)

const skillBars = computed(() =>
  (overview.value?.average_band_by_skill || []).map((s) => ({
    label: capitalizeSkill(s.subject),
    value: s.average_band,
    extra: `${s.attempts} lần`,
    color: skillColor(s.subject),
  }))
)

const bandDonut = computed(() =>
  (overview.value?.band_distribution || []).map((b) => ({
    label: b.label,
    value: b.count,
  }))
)

const subjectBars = computed(() =>
  (overview.value?.attempts_by_subject || []).map((s) => ({
    label: capitalizeSkill(s.subject),
    value: s.attempts,
    extra: `band ${s.average_band}`,
    color: skillColor(s.subject),
  }))
)

function formatShortDate(d) {
  if (!d) return ''
  const s = String(d)
  const dt = new Date(s.includes('T') ? s : `${s}T12:00:00`)
  return `${dt.getDate()}/${dt.getMonth() + 1}`
}

function capitalizeSkill(s) {
  if (!s) return '—'
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function skillColor(subject) {
  const map = {
    reading: '#059669',
    listening: '#3b82f6',
    writing: '#8b5cf6',
    speaking: '#f59e0b',
    vocabulary: '#ec4899',
  }
  return map[(subject || '').toLowerCase()] || '#059669'
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    overview.value = await adminService.getOverview()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không tải được dashboard admin.'
  } finally {
    loading.value = false
  }
})
</script>

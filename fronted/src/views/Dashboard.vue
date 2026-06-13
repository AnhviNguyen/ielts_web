<template>
  <div class="hub-page">
    <section class="section-compact">
      <div class="app-container">
        <div class="spotify-panel">
          <div class="spotify-panel__header">
            <div class="page-header page-header--row" style="margin-bottom: 0">
              <div>
                <h1 class="font-display">Dashboard</h1>
                <p class="page-subtitle">
                  {{ examDateLabel }}
                  <span v-if="ielts.daysToExam !== null"> · {{ ielts.daysToExam }} ngày còn lại</span>
                  <span> · Ôn từ vựng: 10 phút = 1 XP</span>
                </p>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <div class="stat-pill-inline">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--spotify-green)" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                  <span>Streak</span>
                  <strong>{{ ielts.streak }}</strong>
                </div>
                <div class="stat-pill-inline">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--spotify-green)" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                  <span>Target</span>
                  <strong>{{ auth.profile?.target_band ?? '—' }}</strong>
                </div>
              </div>
            </div>
          </div>

          <div class="spotify-panel__tabs">
            <div class="inline-flex rounded-full border border-[var(--border-button)] bg-[var(--bg-surface)] p-1">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                class="flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-medium transition-[background,color] duration-200 ease-in-out"
                :class="activeTab === tab.id
                  ? 'bg-[var(--spotify-green)] font-bold text-black'
                  : 'text-[var(--text-subdued)] hover:bg-[var(--bg-interactive)] hover:text-[var(--text-base)]'"
                @click="activeTab = tab.id"
              >
                <span v-html="tab.icon" class="shrink-0"></span>
                {{ tab.label }}
              </button>
            </div>
          </div>

          <div class="spotify-panel__body">
            <KeepAlive>
              <DashboardHome      v-if="activeTab === 'home'"     key="home" />
              <DashboardReports   v-else-if="activeTab === 'reports'"  key="reports" />
              <DashboardForecast  v-else-if="activeTab === 'forecast'" key="forecast" />
              <DashboardProgress  v-else-if="activeTab === 'progress'" key="progress" />
              <DashboardStudyPlan v-else                               key="study" />
            </KeepAlive>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onActivated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { useIeltsStore } from '@/stores/ielts.js'

import DashboardHome      from '@/components/dashboard/DashboardHome.vue'
import DashboardReports   from '@/components/dashboard/DashboardReports.vue'
import DashboardForecast  from '@/components/dashboard/DashboardForecast.vue'
import DashboardProgress  from '@/components/dashboard/DashboardProgress.vue'
import DashboardStudyPlan from '@/components/dashboard/DashboardStudyPlan.vue'

const auth  = useAuthStore()
const ielts = useIeltsStore()
const route  = useRoute()
const router = useRouter()

const VALID_TABS = new Set(['home', 'reports', 'forecast', 'progress', 'study'])

const activeTab = computed({
  get() {
    const t = route.query.tab
    return VALID_TABS.has(t) ? t : 'home'
  },
  set(val) {
    router.replace({ query: { ...route.query, tab: val } })
  },
})

const TAB_ICONS = {
  home:     `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><polyline points="9 21 9 12 15 12 15 21"/></svg>`,
  reports:  `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19h16M7 16V8M12 16V5M17 16v-3"/></svg>`,
  forecast: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>`,
  progress: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h4l2-5 3 10 2-5h3"/></svg>`,
  study:    `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>`,
}

const tabs = [
  { id: 'home',     label: 'Home',       icon: TAB_ICONS.home     },
  { id: 'reports',  label: 'Reports',    icon: TAB_ICONS.reports  },
  { id: 'forecast', label: 'Dự báo',     icon: TAB_ICONS.forecast },
  { id: 'progress', label: 'Progress',   icon: TAB_ICONS.progress },
  { id: 'study',    label: 'Study Plan', icon: TAB_ICONS.study    },
]

const examDateLabel = computed(() => {
  const d = auth.profile?.exam_date
  if (!d) return 'Chưa đặt ngày thi'
  return new Date(d).toLocaleDateString('vi-VN', { month: 'short', day: 'numeric', year: 'numeric' })
})

async function bootstrapDashboard(full = true) {
  if (!auth.profile) await auth.fetchProfile()
  ielts.targetScores.overall   = Number(auth.profile?.target_band || 7.0)
  ielts.targetScores.reading   = ielts.targetScores.overall
  ielts.targetScores.listening = ielts.targetScores.overall
  ielts.targetScores.writing   = ielts.targetScores.overall
  ielts.targetScores.speaking  = ielts.targetScores.overall

  const jobs = [
    ielts.fetchStats(),
    ielts.fetchHistory(),
    ielts.fetchProgress(),
    auth.fetchProfile(),
  ]
  if (full) {
    jobs.push(
      ielts.fetchPracticeAnalytics(),
      ielts.fetchStudyPlan(),
      ielts.fetchSkillRadar(),
    )
  }
  await Promise.allSettled(jobs)
}

onMounted(() => bootstrapDashboard(true))
onActivated(() => bootstrapDashboard(false))
</script>

<template>
  <div class="grid grid-cols-1 gap-4 xl:grid-cols-[320px_1fr]">
    <!-- Activity Heatmap -->
    <div class="ct-card p-4">
      <div class="mb-3 flex items-center justify-between">
        <div class="text-sm font-bold text-[var(--ink)]">Activity</div>
        <span class="ct-badge" style="background:var(--green-bg);color:var(--green)">{{ streak }} day streak</span>
      </div>
      <HeatmapCalendar :activity-map="ielts.activityMap" compact />

      <!-- Weekly summary -->
      <div v-if="ielts.weeklyStats.length" class="mt-4 border-t border-[var(--border)] pt-3">
        <p class="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--ink3)]">This Week</p>
        <div class="grid grid-cols-7 gap-0.5">
          <div
            v-for="day in ielts.weeklyStats"
            :key="day.date"
            class="flex flex-col items-center gap-1"
          >
            <div
              class="flex h-8 w-full items-end justify-center overflow-hidden rounded-sm"
              title=""
            >
              <div
                class="w-full rounded-sm bg-[#34d399] transition-all"
                :style="{ height: `${dayBarHeight(day)}px`, minHeight: day.time !== '0m' ? '4px' : '0' }"
              ></div>
            </div>
            <span class="text-[9px] text-[var(--ink3)]">{{ day.date }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Progress by skill -->
    <div class="ct-card p-4">
      <div class="mb-4 text-sm font-bold text-[var(--ink)]">Progress by Skill</div>

      <div v-if="!ielts.progress.length" class="flex flex-col items-center justify-center py-10 text-center">
        <div class="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--bg2)] text-[var(--ink3)]">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 12h4l2-5 3 10 2-5h3"/></svg>
        </div>
        <p class="text-[13px] text-[var(--ink2)]">No progress data yet</p>
        <p class="mt-1 text-[11px] text-[var(--ink3)]">Luyện IELTS hoặc ôn từ vựng để theo dõi tiến độ</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="p in ielts.progress"
          :key="p.id || p.subject"
          class="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3.5 transition hover:border-[#34d399]/40 hover:bg-[#f0fdf4]"
        >
          <div class="mb-2 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div
                class="flex h-7 w-7 items-center justify-center rounded-lg text-white"
                :class="skillBg(p.subject)"
              >
                <span v-html="skillIcon(p.subject)"></span>
              </div>
              <span class="text-[13px] font-semibold text-[var(--ink)]">{{ p.subject }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="p.band_score" class="text-[11px] font-bold" :class="bandColor(p.band_score)">
                Band {{ p.band_score }}
              </span>
              <span class="text-[12px] font-bold text-[var(--ink2)]">{{ pct(p) }}%</span>
            </div>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-white">
            <div
              class="h-2 rounded-full bg-[#34d399] transition-all duration-700"
              :style="{ width: `${pct(p)}%` }"
            ></div>
          </div>
          <div class="mt-1.5 flex justify-between text-[10px] text-[var(--ink3)]">
            <span>{{ p.completed_questions ?? 0 }} / {{ p.total_questions ?? 0 }} questions</span>
            <span v-if="p.band_score">Target: {{ targetBand }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useIeltsStore } from '@/stores/ielts.js'
import { useAuthStore } from '@/stores/auth.js'
import HeatmapCalendar from '@/components/ui/HeatmapCalendar.vue'

const ielts = useIeltsStore()
const auth  = useAuthStore()

const streak     = computed(() => ielts.streak || 0)
const targetBand = computed(() => Number(auth.profile?.target_band || 7.0))

function pct(p) {
  return Math.min(100, Math.round(Number(p.percentage || 0)))
}

function dayBarHeight(day) {
  const mins = parseInt(day.time) || 0
  return Math.min(28, Math.round((mins / 90) * 28))
}

function bandColor(val) {
  const n = Number(val)
  if (!n) return 'text-[var(--ink3)]'
  if (n >= 7) return 'text-[#059669]'
  if (n >= 5) return 'text-[#d97706]'
  return 'text-[var(--rose)]'
}

const SKILL_ICONS = {
  Reading:   `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  Listening: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`,
  Writing:   `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  Speaking:  `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></svg>`,
  Vocabulary: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
}
const SKILL_BG = {
  Reading:   'bg-[#2563eb]',
  Listening: 'bg-[#7c3aed]',
  Writing:   'bg-[#d97706]',
  Speaking:  'bg-[#059669]',
  Vocabulary: 'bg-[#0891b2]',
}

function skillIcon(subject) {
  const key = Object.keys(SKILL_ICONS).find(k => k.toLowerCase() === (subject || '').toLowerCase())
  return SKILL_ICONS[key] || SKILL_ICONS.Reading
}
function skillBg(subject) {
  const key = Object.keys(SKILL_BG).find(k => k.toLowerCase() === (subject || '').toLowerCase())
  return SKILL_BG[key] || 'bg-[var(--ink3)]'
}
</script>

<template>
  <div class="space-y-4">
    <!-- Band score cards -->
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
      <BandScoreCard
        label="Overall"
        :score="ielts.bandScores.overall"
        :target="targetBand"
        :overall="true"
      />
      <BandScoreCard label="Reading"   :score="ielts.bandScores.reading"   :target="targetBand" />
      <BandScoreCard label="Listening" :score="ielts.bandScores.listening" :target="targetBand" />
      <BandScoreCard label="Writing"   :score="ielts.bandScores.writing"   :target="targetBand" />
      <BandScoreCard label="Speaking"  :score="ielts.bandScores.speaking"  :target="targetBand" />
    </div>

    <!-- Radar + History grid -->
    <div class="grid grid-cols-1 gap-4 xl:grid-cols-[320px_1fr]">
      <!-- Skill Radar -->
      <div class="ct-card p-5">
        <div class="mb-1 flex items-center justify-between">
          <div class="text-sm font-bold text-[var(--ink)]">Skill Radar</div>
          <span v-if="radarLoading" class="text-[11px] text-[var(--ink3)]">Loading…</span>
          <span v-else class="ct-badge" style="background:var(--green-bg);color:var(--green)">Band 1–9</span>
        </div>
        <p class="mb-4 text-[11px] text-[var(--ink3)]">Average band from your first attempt per quiz</p>

        <div v-if="hasRadarData" class="flex justify-center">
          <SkillRadarChart :scores="radarScores" :target="targetBand" :size="260" />
        </div>
        <div v-else class="flex flex-col items-center justify-center py-10 text-center">
          <div class="mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--bg2)] text-[var(--ink3)]">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19h16M7 16V8M12 16V5M17 16v-3"/></svg>
          </div>
          <p class="text-[13px] font-medium text-[var(--ink2)]">No data yet</p>
          <p class="mt-1 text-[11px] text-[var(--ink3)]">Complete at least one quiz per skill to see your radar chart</p>
        </div>

        <!-- Attempts summary -->
        <div v-if="hasRadarData" class="mt-3 grid grid-cols-2 gap-1.5 border-t border-[var(--border)] pt-3">
          <div
            v-for="skill in skillList"
            :key="skill.key"
            class="flex items-center justify-between rounded-lg bg-[var(--bg)] px-2.5 py-1.5"
          >
            <span class="text-[11px] font-medium text-[var(--ink2)] capitalize">{{ skill.label }}</span>
            <div class="flex items-center gap-1.5">
              <span class="text-[12px] font-bold" :class="bandColor(radarScores[skill.key])">
                {{ radarScores[skill.key] ? radarScores[skill.key].toFixed(1) : '—' }}
              </span>
              <span class="text-[10px] text-[var(--ink3)]">({{ ielts.skillRadar.attempts?.[skill.key] || 0 }} quizzes)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- History table -->
      <div class="ct-card overflow-hidden">
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <div class="text-sm font-bold text-[var(--ink)]">Recent Attempts</div>
          <RouterLink to="/history" class="text-[11px] font-medium text-[#34d399] hover:text-[#059669]">View all →</RouterLink>
        </div>

        <div v-if="!ielts.history.length" class="flex flex-col items-center justify-center py-12 text-center">
          <div class="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--bg2)] text-[var(--ink3)]">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <p class="text-[13px] text-[var(--ink2)]">No attempts yet</p>
          <p class="mt-1 text-[11px] text-[var(--ink3)]">Start practicing to see your history here</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full border-collapse text-[12px]">
            <thead>
              <tr class="border-b border-[var(--border)] bg-[var(--bg)] text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--ink3)]">
                <th class="px-4 py-2.5">Date</th>
                <th class="px-4 py-2.5">Skill</th>
                <th class="px-4 py-2.5">Score</th>
                <th class="px-4 py-2.5">Band</th>
                <th class="px-4 py-2.5">Mode</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in ielts.history.slice(0, 15)"
                :key="row.id"
                class="border-b border-[var(--border)] transition hover:bg-[#f0fdf4]"
              >
                <td class="px-4 py-2.5 text-[var(--ink3)]">{{ formatDate(row.date) }}</td>
                <td class="px-4 py-2.5">
                  <span class="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium capitalize" :class="skillBadgeClass(row.skill)">
                    {{ row.skill }}
                  </span>
                </td>
                <td class="px-4 py-2.5 font-medium text-[var(--ink)]">{{ row.score ?? '—' }}</td>
                <td class="px-4 py-2.5">
                  <span class="font-bold" :class="bandColor(row.band_score ?? row.score)">
                    {{ row.band_score ?? row.score ?? '—' }}
                  </span>
                </td>
                <td class="px-4 py-2.5">
                  <span class="rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase"
                    :class="row.mode === 'exam' ? 'bg-[#111] text-white' : 'bg-[var(--bg2)] text-[var(--ink3)]'">
                    {{ row.mode || 'practice' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useIeltsStore } from '@/stores/ielts.js'
import { useAuthStore } from '@/stores/auth.js'
import BandScoreCard from '@/components/ui/BandScoreCard.vue'
import SkillRadarChart from '@/components/dashboard/SkillRadarChart.vue'

const ielts = useIeltsStore()
const auth  = useAuthStore()

const radarLoading = ref(false)

const targetBand = computed(() => Number(auth.profile?.target_band || 7.0))

const radarScores = computed(() => ({
  reading:   ielts.skillRadar.reading   || 0,
  listening: ielts.skillRadar.listening || 0,
  writing:   ielts.skillRadar.writing   || 0,
  speaking:  ielts.skillRadar.speaking  || 0,
}))

const hasRadarData = computed(() =>
  Object.values(radarScores.value).some(v => v > 0)
)

const skillList = [
  { key: 'reading',   label: 'Reading'   },
  { key: 'listening', label: 'Listening' },
  { key: 'writing',   label: 'Writing'   },
  { key: 'speaking',  label: 'Speaking'  },
]

function formatDate(d) {
  if (!d) return '—'
  return String(d).slice(0, 10)
}

function bandColor(val) {
  const n = Number(val)
  if (!n) return 'text-[var(--ink3)]'
  if (n >= 7) return 'text-[#059669]'
  if (n >= 5) return 'text-[#d97706]'
  return 'text-[var(--rose)]'
}

function skillBadgeClass(skill) {
  const map = {
    reading:   'bg-[#eff6ff] text-[#2563eb]',
    listening: 'bg-[#f5f3ff] text-[#7c3aed]',
    writing:   'bg-[#fff7ed] text-[#d97706]',
    speaking:  'bg-[#f0fdf4] text-[#059669]',
    vocabulary: 'bg-[#ecfeff] text-[#0891b2]',
  }
  return map[skill] || 'bg-[var(--bg2)] text-[var(--ink3)]'
}

onMounted(async () => {
  if (!Object.values(radarScores.value).some(v => v > 0)) {
    radarLoading.value = true
    await ielts.fetchSkillRadar()
    radarLoading.value = false
  }
})
</script>

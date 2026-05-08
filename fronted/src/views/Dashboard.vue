<template>
  <div class="space-y-4">
    <!-- Tabs -->
    <div class="inline-flex rounded-md border border-[var(--border)] bg-white p-1">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="flex items-center gap-1.5 rounded px-3.5 py-1.5 text-[13px] font-medium transition-colors"
        :class="activeTab === tab.id ? 'border border-[#34d399] bg-[#34d39912] text-[#34d399]' : 'text-[var(--ink2)] hover:bg-[var(--bg2)]'"
        @click="activeTab = tab.id"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path v-if="tab.id === 'home'" d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>
          <path v-else-if="tab.id === 'reports'" d="M4 19h16M7 16V8M12 16V5M17 16v-3"/>
          <path v-else-if="tab.id === 'progress'" d="M5 12h4l2-5 3 10 2-5h3"/>
          <path v-else d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>
        </svg>
        {{ tab.label }}
      </button>
    </div>

    <!-- Header card (real profile stats) -->
    <div class="rounded-lg border border-[var(--border)] bg-white p-3.5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="text-lg font-semibold text-[var(--ink)]">IELTS Academic</div>
          <div class="text-[13px] text-[var(--ink3)]">
            {{ examDateLabel }}
            <span v-if="ielts.daysToExam !== null"> ({{ ielts.daysToExam }} days left)</span>
          </div>
        </div>
        <div class="rounded-md bg-[var(--bg)] px-3 py-1.5 text-[13px] text-[var(--ink2)]">
          Overall target:
          <strong class="text-[var(--ink)]">{{ auth.profile?.target_band ?? '—' }}</strong>
          <span class="mx-2 text-[var(--border2)]">|</span>
          Streak:
          <strong class="text-[var(--ink)]">{{ ielts.streak }}</strong>
        </div>
      </div>
    </div>

    <!-- HOME -->
    <template v-if="activeTab === 'home'">
      <div class="rounded-lg border border-[var(--border)] bg-white p-5 text-center">
        <div class="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#34d39955] bg-[#34d39912] text-[#34d399]">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="8" width="16" height="11" rx="4"/><path d="M9 8V5a3 3 0 0 1 6 0v3"/><circle cx="9.5" cy="13" r="1"/><circle cx="14.5" cy="13" r="1"/><path d="M9 16c1 .8 2 .8 3 .8s2 0 3-.8"/>
          </svg>
        </div>
        <h2 class="text-3xl font-semibold text-[var(--ink)]">Hey, I'm Catbot!</h2>
        <p class="mt-1.5 text-lg text-[var(--ink2)]">I'm here to make IELTS prep effective for you.</p>

        <div class="mx-auto mt-5 max-w-3xl rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3.5">
          <div class="flex gap-2">
            <input
              v-model="chatInput"
              class="ct-input flex-1"
              placeholder="Ask anything in your language"
              :disabled="chatLoading"
              @keydown.enter.prevent="sendDashboardChat"
            />
            <button
              class="flex items-center justify-center rounded-md border border-[#34d399] bg-[#34d399] px-3.5 text-white transition hover:bg-[#10b981] disabled:opacity-40"
              :disabled="chatLoading || !chatInput.trim()"
              @click="sendDashboardChat"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13"/><path d="M22 2L15 22l-4-9-9-4z"/></svg>
            </button>
          </div>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="q in quickPrompts"
              :key="q"
              class="rounded-full border border-[var(--border2)] px-2.5 py-1 text-[11px] text-[var(--ink2)]"
              :disabled="chatLoading"
              @click="sendDashboardPrompt(q)"
            >
              {{ q }}
            </button>
          </div>
          <div v-if="chatReply" class="mt-3 rounded-md border border-[var(--border)] bg-white p-3 text-left text-[13px] text-[var(--ink)]">
            {{ chatReply }}
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-[var(--border)] bg-white p-4.5">
        <div class="mb-2 text-2xl font-semibold text-[var(--ink)]">Getting Started <span class="text-[#34d399]">{{ completionPct }}%</span></div>
        <div class="h-2 rounded-full bg-[var(--bg2)]">
          <div class="h-2 rounded-full bg-[#34d399] transition-all" :style="{ width: `${completionPct}%` }"></div>
        </div>
        <div class="mt-4 space-y-2">
          <div v-for="task in gettingStarted" :key="task.label" class="flex items-center justify-between rounded-md bg-[var(--bg)] px-3.5 py-2.5">
            <span class="text-[var(--ink)]">{{ task.label }}</span>
            <span :class="task.done ? 'text-[#22c55e]' : 'text-[var(--ink3)]'">
              <svg v-if="task.done" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
              <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- REPORTS -->
    <template v-else-if="activeTab === 'reports'">
      <div class="grid grid-cols-1 gap-3 xl:grid-cols-5">
        <BandScoreCard label="Overall" :score="ielts.bandScores.overall" :target="targetBand" :overall="true" />
        <BandScoreCard label="Reading" :score="ielts.bandScores.reading" :target="targetBand" color-hex="var(--ink)" />
        <BandScoreCard label="Listening" :score="ielts.bandScores.listening" :target="targetBand" color-hex="var(--ink)" />
        <BandScoreCard label="Writing" :score="ielts.bandScores.writing" :target="targetBand" color-hex="var(--ink)" />
        <BandScoreCard label="Speaking" :score="ielts.bandScores.speaking" :target="targetBand" color-hex="var(--ink)" />
      </div>

      <div class="overflow-hidden rounded-lg border border-[var(--border)] bg-white">
        <table class="w-full border-collapse text-sm">
          <thead>
            <tr class="bg-[var(--bg)] text-left text-xs text-[var(--ink3)]">
              <th class="px-4 py-3">Date</th>
              <th class="px-4 py-3">Skill</th>
              <th class="px-4 py-3">Score</th>
              <th class="px-4 py-3">Band</th>
              <th class="px-4 py-3">Mode</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in ielts.history.slice(0, 12)" :key="row.id" class="border-t border-[var(--border)]">
              <td class="px-4 py-3">{{ row.date ? String(row.date).slice(0, 10) : '—' }}</td>
              <td class="px-4 py-3 capitalize">{{ row.skill }}</td>
              <td class="px-4 py-3">{{ row.score }}</td>
              <td class="px-4 py-3">{{ row.band_score ?? row.score ?? '—' }}</td>
              <td class="px-4 py-3">{{ row.mode || 'practice' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- PROGRESS -->
    <template v-else-if="activeTab === 'progress'">
      <div class="grid grid-cols-1 gap-4 xl:grid-cols-[300px_1fr]">
        <div class="rounded-lg border border-[var(--border)] bg-white p-3.5">
          <HeatmapCalendar :activity-map="ielts.activityMap" compact />
        </div>
        <div class="rounded-lg border border-[var(--border)] bg-white p-3.5">
          <div class="mb-3 text-sm font-semibold text-[var(--ink)]">Progress by skill</div>
          <div class="space-y-3">
            <div v-for="p in ielts.progress" :key="p.id || p.subject" class="rounded-md border border-[var(--border)] bg-[var(--bg)] p-2.5">
              <div class="mb-1 flex items-center justify-between text-sm">
                <span class="font-medium text-[var(--ink)]">{{ p.subject }}</span>
                <span class="text-[var(--ink2)]">{{ Number(p.percentage || 0).toFixed(0) }}%</span>
              </div>
              <div class="h-1.5 rounded-full bg-white">
                <div class="h-1.5 rounded-full bg-[#34d399]" :style="{ width: `${Math.min(100, Number(p.percentage || 0))}%` }"></div>
              </div>
            </div>
            <div v-if="!ielts.progress.length" class="text-sm text-[var(--ink3)]">No progress data yet.</div>
          </div>
        </div>
      </div>
    </template>

    <!-- STUDY PLAN -->
    <template v-else>
      <div class="rounded-lg border border-[var(--border)] bg-white p-3.5">
        <div class="mb-3 flex items-center justify-between">
          <div class="text-sm font-semibold text-[var(--ink)]">Study Plan</div>
          <button class="ct-btn px-3 py-1 text-xs" @click="generatePlan">Generate plan</button>
        </div>
        <div class="space-y-2">
          <div
            v-for="d in ielts.studyPlan.days || []"
            :key="d.day"
            class="flex items-center justify-between rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
          >
            <span>Day {{ d.day }} · {{ d.focus }}</span>
            <strong>{{ d.minutes }} min</strong>
          </div>
          <div v-if="!(ielts.studyPlan.days || []).length" class="text-sm text-[var(--ink3)]">
            {{ ielts.studyPlan.message || 'No study plan yet.' }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import { useIeltsStore } from '@/stores/ielts.js'
import { ieltsService } from '@/services/ieltsService.js'
import BandScoreCard from '@/components/ui/BandScoreCard.vue'
import HeatmapCalendar from '@/components/ui/HeatmapCalendar.vue'

const auth = useAuthStore()
const ielts = useIeltsStore()

const tabs = [
  { id: 'home', label: 'Home' },
  { id: 'reports', label: 'Reports' },
  { id: 'progress', label: 'Progress' },
  { id: 'study', label: 'Study Plan' },
]
const activeTab = ref('home')

const chatInput = ref('')
const chatReply = ref('')
const chatLoading = ref(false)
const chatHistory = ref([])
const quickPrompts = ['How to improve speaking?', 'Give me today plan', 'How do I raise writing score?']

const targetBand = computed(() => Number(auth.profile?.target_band || 7.0))
const examDateLabel = computed(() => {
  const d = auth.profile?.exam_date
  if (!d) return 'No exam date set'
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const hasSpeaking = computed(() => ielts.history.some(h => h.skill === 'speaking'))
const hasWriting = computed(() => ielts.history.some(h => h.skill === 'writing'))
const gettingStarted = computed(() => ([
  { label: 'Add your target score', done: !!auth.profile?.target_band },
  { label: 'Learn your speaking level', done: hasSpeaking.value },
  { label: 'Learn your writing level', done: hasWriting.value },
]))
const completionPct = computed(() => {
  const done = gettingStarted.value.filter(x => x.done).length
  return Math.round((done / gettingStarted.value.length) * 100)
})

async function sendDashboardPrompt(text) {
  chatInput.value = text
  await sendDashboardChat()
}

async function sendDashboardChat() {
  const t = chatInput.value.trim()
  if (!t || chatLoading.value) return
  chatLoading.value = true
  try {
    const data = await ieltsService.askDashboardCoach({
      userMessage: t,
      history: chatHistory.value,
    })
    chatReply.value = data.reply || data.error || 'No response.'
    chatHistory.value.push({ role: 'user', content: t })
    chatHistory.value.push({ role: 'assistant', content: chatReply.value })
    chatInput.value = ''
  } catch {
    chatReply.value = 'Chatbot is unavailable right now.'
  } finally {
    chatLoading.value = false
  }
}

async function generatePlan() {
  await ielts.generateStudyPlan()
}

onMounted(async () => {
  if (!auth.profile) await auth.fetchProfile()
  ielts.targetScores.overall = Number(auth.profile?.target_band || 7.0)
  ielts.targetScores.reading = ielts.targetScores.overall
  ielts.targetScores.listening = ielts.targetScores.overall
  ielts.targetScores.writing = ielts.targetScores.overall
  ielts.targetScores.speaking = ielts.targetScores.overall

  await Promise.all([
    ielts.fetchStats(),
    ielts.fetchHistory(),
    ielts.fetchProgress(),
    ielts.fetchPracticeAnalytics(),
    ielts.fetchStudyPlan(),
  ])
})
</script>

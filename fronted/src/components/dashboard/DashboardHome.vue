<template>
  <div class="space-y-4">
    <PlacementPromptBanner />

    <!-- Next-week prediction summary -->
    <NextWeekMiniBanner />

    <!-- Catbot card -->
    <div class="ct-card overflow-hidden" data-tour="dashboard-catbot">
      <!-- Header -->
      <div class="catbot-header flex items-center justify-center gap-3 border-b px-5 py-4 text-center">
        <img src="/icon_profile.jpg" alt="Catbot" class="h-10 w-10 shrink-0 rounded-full object-cover shadow-sm ring-2 ring-[var(--spotify-green)]" />
        <div>
          <div class="catbot-title text-base font-bold">Catbot</div>
          <div class="catbot-subtitle flex items-center justify-center gap-1.5 text-[11px]">
            <span class="inline-block h-1.5 w-1.5 rounded-full bg-[var(--spotify-green)]"></span>
            IELTS Coach · always online
          </div>
        </div>
      </div>

      <!-- Message thread -->
      <div ref="threadRef" class="flex max-h-72 flex-col gap-2 overflow-y-auto bg-[var(--bg)] px-4 py-3">
        <!-- Welcome message -->
        <div class="flex gap-2">
          <img src="/icon_profile.jpg" alt="Catbot" class="h-7 w-7 shrink-0 rounded-full object-cover ring-1 ring-[var(--spotify-green)]" />
          <div class="catbot-bubble-assistant max-w-[75%] rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-[13px]">
            Hey! I'm Catbot 👋 I'm here to make your IELTS prep effective. Ask me anything or pick a quick question below.
          </div>
        </div>

        <!-- Dynamic messages -->
        <template v-for="(msg, i) in chatHistory" :key="i">
          <!-- User -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="chat-bubble-user max-w-[75%] rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-[13px] shadow-sm">
              {{ msg.content }}
            </div>
          </div>
          <!-- Assistant -->
          <div v-else class="flex gap-2">
            <img src="/icon_profile.jpg" alt="Catbot" class="h-7 w-7 shrink-0 rounded-full object-cover ring-1 ring-[var(--spotify-green)]" />
            <div class="catbot-bubble-assistant max-w-[75%] rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-[13px] leading-relaxed" style="white-space: pre-wrap">{{ msg.content }}</div>
          </div>
        </template>

        <!-- Loading indicator -->
        <div v-if="chatLoading" class="flex gap-2">
          <img src="/icon_profile.jpg" alt="Catbot" class="h-7 w-7 shrink-0 rounded-full object-cover ring-1 ring-[var(--spotify-green)]" />
          <div class="catbot-bubble-assistant flex items-center gap-1 rounded-2xl rounded-tl-sm px-3.5 py-3">
            <span v-for="n in 3" :key="n" class="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--spotify-green)]" :style="{ animationDelay: `${(n-1)*0.15}s` }"></span>
          </div>
        </div>
      </div>

      <!-- Quick prompts -->
      <div class="flex flex-wrap gap-1.5 border-t border-[var(--border)] px-4 py-2">
        <button
          v-for="q in quickPrompts" :key="q"
          class="rounded-full border border-[var(--border2)] bg-[var(--bg-surface)] px-2.5 py-1 text-[11px] text-[var(--text-subdued)] transition-all duration-200 hover:border-[var(--spotify-green)] hover:text-[var(--spotify-green)]"
          :disabled="chatLoading"
          @click="sendPrompt(q)"
        >
          {{ q }}
        </button>
      </div>

      <!-- Input bar -->
      <div class="flex gap-2 border-t border-[var(--border)] bg-[var(--bg-surface)] px-3 py-3">
        <input
          v-model="chatInput"
          class="ct-input flex-1 text-[13px]"
          placeholder="Ask anything about IELTS…"
          :disabled="chatLoading"
          @keydown.enter.prevent="sendChat"
        />
        <button
          class="btn btn-primary flex h-9 w-9 shrink-0 items-center justify-center !rounded-full !p-0 disabled:opacity-40"
          :disabled="chatLoading || !chatInput.trim()"
          @click="sendChat"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 2L11 13"/><path d="M22 2L15 22l-4-9-9-4z"/></svg>
        </button>
      </div>
    </div>

    <!-- Skills quick access -->
    <div class="ct-card p-5" data-tour="dashboard-skills">
      <div class="mb-3 text-sm font-bold text-[var(--ink)]">Kỹ năng IELTS</div>
      <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
        <RouterLink
          v-for="skill in skillLinks"
          :key="skill.path"
          :to="skill.path"
          class="accent-hover group flex flex-col items-center gap-2 rounded-[var(--radius-comfortable)] border border-[var(--border)] bg-[var(--bg)] p-3 text-center transition-all duration-200"
        >
          <div
            class="flex h-9 w-9 items-center justify-center rounded-lg text-white"
            :style="{ background: skill.color }"
          >
            <span v-html="skill.icon"></span>
          </div>
          <span class="text-[12px] font-semibold text-[var(--ink)]">{{ skill.label }}</span>
        </RouterLink>
      </div>
    </div>

    <!-- Getting Started -->
    <div class="ct-card p-5">
      <div class="mb-1 flex items-center justify-between">
        <div class="text-base font-bold text-[var(--ink)]">Getting Started</div>
        <span class="ct-badge" style="background:var(--green-bg);color:var(--green)">{{ completionPct }}%</span>
      </div>
      <p class="mb-4 text-[12px] text-[var(--ink3)]">Hoàn thành các bước IELTS và ôn từ vựng (10 phút = 1 XP)</p>

      <!-- Progress bar -->
      <div class="mb-4 h-1.5 overflow-hidden rounded-full bg-[var(--bg2)]">
        <div
          class="h-1.5 rounded-full bg-[var(--spotify-green)] transition-all duration-200"
          :style="{ width: `${completionPct}%` }"
        ></div>
      </div>

      <div class="space-y-2">
        <RouterLink
          v-for="task in tasks"
          :key="task.label"
          :to="task.route"
          class="accent-hover group flex items-center justify-between rounded-[var(--radius-comfortable)] border border-[var(--border)] bg-[var(--bg)] px-4 py-3 transition-all duration-200"
          :class="task.done ? 'opacity-70' : ''"
        >
          <div class="flex items-center gap-3 min-w-0">
            <!-- Skill icon -->
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
              :class="task.done ? 'bg-[var(--green-bg)] text-[var(--spotify-green)]' : 'bg-[var(--bg2)] text-[var(--text-subdued)] group-hover:bg-[var(--green-bg)] group-hover:text-[var(--spotify-green)]'"
            >
              <span v-html="task.icon"></span>
            </div>
            <div class="min-w-0">
              <div
                class="text-[13px] font-medium text-[var(--ink)] transition"
                :class="task.done ? 'line-through decoration-[var(--rose)] decoration-2' : ''"
              >
                {{ task.label }}
              </div>
              <div class="text-[11px] text-[var(--ink3)]">{{ task.hint }}</div>
            </div>
          </div>
          <!-- Status icon -->
          <div class="ml-3 shrink-0">
            <div v-if="task.done" class="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--green-bg)]">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--spotify-green)" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
            </div>
            <div v-else class="flex h-6 w-6 items-center justify-center rounded-full border border-[var(--border2)] text-[var(--text-subdued)] transition-all duration-200 group-hover:border-[var(--spotify-green)] group-hover:text-[var(--spotify-green)]">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
            </div>
          </div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useIeltsStore } from '@/stores/ielts.js'
import { useAuthStore } from '@/stores/auth.js'
import { ieltsService } from '@/services/ieltsService.js'
import NextWeekMiniBanner from '@/components/dashboard/NextWeekMiniBanner.vue'
import PlacementPromptBanner from '@/components/onboarding/PlacementPromptBanner.vue'

const ielts = useIeltsStore()
const auth  = useAuthStore()

// ── Chat ──────────────────────────────────────────────────────────
const chatInput   = ref('')
const chatLoading = ref(false)
const chatHistory = ref([])
const threadRef   = ref(null)

const quickPrompts = [
  'How to improve speaking?',
  'Give me a plan for today',
  'How do I raise writing score?',
  'What should I focus on first?',
]

async function sendPrompt(text) {
  chatInput.value = text
  await sendChat()
}

async function sendChat() {
  const text = chatInput.value.trim()
  if (!text || chatLoading.value) return
  chatLoading.value = true
  chatHistory.value.push({ role: 'user', content: text })
  chatInput.value = ''
  await scrollThread()
  try {
    const data = await ieltsService.askDashboardCoach({
      userMessage: text,
      history: chatHistory.value.slice(-10),
    })
    chatHistory.value.push({ role: 'assistant', content: data.reply || data.error || 'No response.' })
  } catch {
    chatHistory.value.push({ role: 'assistant', content: 'Catbot is unavailable right now. Please try again later.' })
  } finally {
    chatLoading.value = false
    await scrollThread()
  }
}

async function scrollThread() {
  await nextTick()
  if (threadRef.value) threadRef.value.scrollTop = threadRef.value.scrollHeight
}

watch(() => chatHistory.value.length, scrollThread)

// ── Getting Started tasks (reset daily at midnight) ──────────────
function getTodayStr() {
  return new Date().toISOString().slice(0, 10)
}

function isToday(dateStr) {
  if (!dateStr) return false
  return String(dateStr).slice(0, 10) === getTodayStr()
}

// Tasks check if the user completed an activity TODAY
const hasSpeaking   = computed(() => ielts.history.some(h => h.skill === 'speaking' && isToday(h.date)))
const hasWriting    = computed(() => ielts.history.some(h => h.skill === 'writing' && isToday(h.date)))
const hasReading    = computed(() => ielts.history.some(h => h.skill === 'reading' && isToday(h.date)))
const hasListening  = computed(() => ielts.history.some(h => h.skill === 'listening' && isToday(h.date)))
const hasVocabulary = computed(() => ielts.history.some(h => h.skill === 'vocabulary' && isToday(h.date)))
const hasTargetBand = computed(() => !!auth.profile?.target_band)

// Schedule refresh at next midnight for daily reset
onMounted(() => {
  const now = new Date()
  const nextMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0)
  const msUntilMidnight = nextMidnight - now
  setTimeout(async () => {
    await ielts.fetchHistory()
  }, msUntilMidnight)
})

const skillLinks = [
  {
    label: 'Reading',
    path: '/reading',
    color: '#2563eb',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  },
  {
    label: 'Listening',
    path: '/listening',
    color: '#7c3aed',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`,
  },
  {
    label: 'Writing',
    path: '/writing',
    color: '#d97706',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  },
  {
    label: 'Speaking',
    path: '/speaking',
    color: '#059669',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
  },
  {
    label: 'Từ vựng',
    path: '/vocabulary',
    color: '#0891b2',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
  },
]

const ICONS = {
  profile: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>`,
  speaking: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
  writing: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  reading: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  listening: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`,
  vocabulary: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
}

const tasks = computed(() => [
  {
    label: 'Set your target band score',
    hint:  'Go to Profile and set your IELTS goal',
    route: '/profile',
    done:  hasTargetBand.value,
    icon:  ICONS.profile,
  },
  {
    label: 'Complete a Speaking session',
    hint:  'Find out your speaking level',
    route: '/speaking',
    done:  hasSpeaking.value,
    icon:  ICONS.speaking,
  },
  {
    label: 'Complete a Writing session',
    hint:  'Get AI feedback on your writing',
    route: '/writing',
    done:  hasWriting.value,
    icon:  ICONS.writing,
  },
  {
    label: 'Complete a Reading test',
    hint:  'Practice Cambridge-style passages',
    route: '/reading',
    done:  hasReading.value,
    icon:  ICONS.reading,
  },
  {
    label: 'Complete a Listening test',
    hint:  'Train your listening comprehension',
    route: '/listening',
    done:  hasListening.value,
    icon:  ICONS.listening,
  },
  {
    label: 'Review vocabulary today',
    hint:  'SRS flashcard · 10 phút = 1 XP',
    route: '/vocabulary',
    done:  hasVocabulary.value,
    icon:  ICONS.vocabulary,
  },
])

const completionPct = computed(() => {
  const done = tasks.value.filter(t => t.done).length
  return Math.round((done / tasks.value.length) * 100)
})
</script>

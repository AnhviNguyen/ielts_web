<template>
  <div class="space-y-4">
    <!-- Header bar -->
    <div class="ct-card flex flex-wrap items-center justify-between gap-3 px-5 py-4">
      <div>
        <div class="flex items-center gap-2">
          <div class="text-base font-bold text-[var(--ink)]">Study Plan</div>
          <span v-if="totalTasks" class="ct-badge" style="background:var(--green-bg);color:var(--green)">
            {{ completedTasks }}/{{ totalTasks }} done
          </span>
        </div>
        <p class="mt-0.5 text-[12px] text-[var(--ink3)]">AI-generated personalised roadmap based on your history</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="ct-btn px-3.5 py-2 text-[12px]"
          :disabled="generating"
          @click="handleGenerate"
        >
          <svg v-if="generating" class="mr-1.5 inline h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          <svg v-else class="mr-1.5 inline h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
          {{ hasPlan ? 'Regenerate' : 'Generate Plan' }}
        </button>
        <button
          v-if="hasPlan"
          class="ct-btn px-3.5 py-2 text-[12px]"
          :disabled="extending"
          @click="handleExtend"
        >
          <svg v-if="extending" class="mr-1.5 inline h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          <svg v-else class="mr-1.5 inline h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          Add 5 more days
        </button>
      </div>
    </div>

    <!-- Overall progress bar -->
    <div v-if="totalTasks" class="ct-card px-5 py-3">
      <div class="mb-1.5 flex items-center justify-between text-[12px]">
        <span class="font-medium text-[var(--ink2)]">Overall completion</span>
        <span class="font-bold text-[#059669]">{{ Math.round((completedTasks / totalTasks) * 100) }}%</span>
      </div>
      <div class="h-2 overflow-hidden rounded-full bg-[var(--bg2)]">
        <div
          class="h-2 rounded-full bg-[#34d399] transition-all duration-700"
          :style="{ width: `${(completedTasks / totalTasks) * 100}%` }"
        ></div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!hasPlan && !generating" class="ct-card flex flex-col items-center justify-center py-16 text-center">
      <div class="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-[#f0fdf4] text-[#34d399]">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
      </div>
      <p class="text-[15px] font-semibold text-[var(--ink)]">No plan yet</p>
      <p class="mt-1.5 max-w-xs text-[13px] text-[var(--ink3)]">Click "Generate Plan" to create a personalised AI study plan based on your skill levels and history.</p>
    </div>

    <!-- Generating skeleton -->
    <div v-if="generating" class="space-y-3">
      <div v-for="i in 5" :key="i" class="ct-card animate-pulse p-4">
        <div class="mb-2 h-4 w-24 rounded bg-[var(--bg2)]"></div>
        <div class="h-3 w-full rounded bg-[var(--bg2)]"></div>
        <div class="mt-1.5 h-3 w-3/4 rounded bg-[var(--bg2)]"></div>
      </div>
    </div>

    <!-- Day groups -->
    <div v-if="!generating && hasPlan" class="space-y-3">
      <div
        v-for="dayGroup in ielts.studyPlanData.days"
        :key="dayGroup.day_number"
        class="ct-card overflow-hidden"
      >
        <!-- Day header -->
        <div
          class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3"
          :class="isDayComplete(dayGroup) ? 'bg-[#f0fdf4]' : 'bg-[var(--bg)]'"
        >
          <div class="flex items-center gap-2">
            <div
              class="flex h-7 w-7 items-center justify-center rounded-full text-[12px] font-bold"
              :class="isDayComplete(dayGroup) ? 'bg-[#34d399] text-white' : 'bg-[var(--bg2)] text-[var(--ink2)]'"
            >
              {{ dayGroup.day_number }}
            </div>
            <div>
              <span class="text-[13px] font-bold text-[var(--ink)]">Day {{ dayGroup.day_number }}</span>
              <span v-if="dayGroup.plan_date" class="ml-2 text-[11px] text-[var(--ink3)]">{{ formatDate(dayGroup.plan_date) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <!-- Skill badge -->
            <span
              class="rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
              :class="skillBadge(primarySkill(dayGroup))"
            >
              {{ primarySkill(dayGroup) }}
            </span>
            <!-- Day completion icon -->
            <div v-if="isDayComplete(dayGroup)" class="flex h-5 w-5 items-center justify-center rounded-full bg-[#34d399]">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
            </div>
          </div>
        </div>

        <!-- Tasks -->
        <div class="divide-y divide-[var(--border)]">
          <div
            v-for="task in dayGroup.tasks"
            :key="task.id"
            class="group flex items-start gap-3 px-4 py-3 transition"
            :class="task.is_completed ? 'bg-[#fafffe]' : 'hover:bg-[#f8fffe]'"
          >
            <!-- Checkbox -->
            <button
              class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition"
              :class="task.is_completed
                ? 'border-[#34d399] bg-[#34d399]'
                : 'border-[var(--border2)] hover:border-[#34d399]'"
              @click="toggleTask(task)"
            >
              <svg v-if="task.is_completed" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3.5"><path d="M20 6L9 17l-5-5"/></svg>
            </button>

            <!-- Content -->
            <div class="min-w-0 flex-1">
              <div
                class="text-[13px] font-medium leading-snug text-[var(--ink)] transition"
                :class="task.is_completed ? 'line-through decoration-[var(--rose)] decoration-2 opacity-60' : ''"
              >
                {{ task.task_description }}
              </div>
              <div class="mt-1 flex items-center gap-2.5 text-[11px] text-[var(--ink3)]">
                <span class="flex items-center gap-1">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  {{ task.duration_minutes }} min
                </span>
                <span class="flex items-center gap-1 capitalize">
                  <span class="inline-block h-1.5 w-1.5 rounded-full" :class="skillDot(task.focus_skill)"></span>
                  {{ task.focus_skill }}
                </span>
                <span v-if="task.is_completed" class="text-[var(--rose)]">✓ Completed</span>
              </div>
            </div>

            <!-- Go button -->
            <RouterLink
              v-if="task.route_path && !task.is_completed"
              :to="task.route_path"
              class="ml-2 shrink-0 rounded-lg border border-[var(--border2)] bg-white px-2.5 py-1 text-[11px] font-medium text-[var(--ink2)] opacity-0 transition group-hover:opacity-100 hover:border-[#34d399] hover:text-[#059669]"
            >
              Go →
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useIeltsStore } from '@/stores/ielts.js'

const ielts = useIeltsStore()

const generating = ref(false)
const extending  = ref(false)

const hasPlan = computed(() => (ielts.studyPlanData.days || []).length > 0)
const totalTasks = computed(() => ielts.studyPlanData.total_tasks || 0)
const completedTasks = computed(() => ielts.studyPlanData.completed_tasks || 0)

async function handleGenerate() {
  generating.value = true
  await ielts.generateStudyPlan()
  generating.value = false
}

async function handleExtend() {
  extending.value = true
  await ielts.extendStudyPlan()
  extending.value = false
}

async function toggleTask(task) {
  await ielts.completeStudyTask(task.id)
}

function isDayComplete(dayGroup) {
  return dayGroup.tasks.length > 0 && dayGroup.tasks.every(t => t.is_completed)
}

function primarySkill(dayGroup) {
  return dayGroup.tasks[0]?.focus_skill || 'reading'
}

function formatDate(d) {
  if (!d) return ''
  const dt = new Date(d)
  return dt.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

const SKILL_BADGE = {
  reading:   'bg-[#eff6ff] text-[#2563eb]',
  listening: 'bg-[#f5f3ff] text-[#7c3aed]',
  writing:   'bg-[#fff7ed] text-[#d97706]',
  speaking:  'bg-[#f0fdf4] text-[#059669]',
  vocabulary: 'bg-[#ecfeff] text-[#0891b2]',
}
const SKILL_DOT = {
  reading:   'bg-[#2563eb]',
  listening: 'bg-[#7c3aed]',
  writing:   'bg-[#d97706]',
  speaking:  'bg-[#34d399]',
  vocabulary: 'bg-[#0891b2]',
}

function skillBadge(skill) {
  return SKILL_BADGE[skill] || 'bg-[var(--bg2)] text-[var(--ink3)]'
}
function skillDot(skill) {
  return SKILL_DOT[skill] || 'bg-[var(--ink3)]'
}
</script>

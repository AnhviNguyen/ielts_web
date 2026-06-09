<template>
  <div v-if="visible" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/45 px-4 py-6">
    <section class="w-full max-w-2xl overflow-hidden rounded-xl border border-[var(--border)] bg-white shadow-2xl">
      <header class="border-b border-[var(--border)] px-5 py-4">
        <div class="text-sm font-bold uppercase tracking-wide text-[#059669]">Initial IELTS band</div>
        <h2 class="mt-1 text-xl font-bold text-[var(--ink)]">Set your starting point</h2>
        <p class="mt-1 text-sm text-[var(--ink3)]">
          Take a full placement mock test or enter your existing IELTS bands before continuing.
        </p>
      </header>

      <div class="p-5">
        <div v-if="placement.error || error" class="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {{ placement.error || error }}
        </div>

        <div v-if="mode === 'choice'" class="grid gap-3 sm:grid-cols-2">
          <button type="button" class="choice-card" :disabled="loading" @click="startFullPlacement">
            <span class="choice-card__icon">01</span>
            <span class="choice-card__title">Take full placement test</span>
            <span class="choice-card__body">The system randomly selects one existing full mock exam.</span>
          </button>
          <button type="button" class="choice-card" :disabled="loading" @click="mode = 'manual'">
            <span class="choice-card__icon">02</span>
            <span class="choice-card__title">Enter existing scores</span>
            <span class="choice-card__body">Use your known IELTS bands for all four skills.</span>
          </button>
        </div>

        <form v-else class="space-y-4" @submit.prevent="submitManual">
          <div class="grid gap-3 sm:grid-cols-4">
            <label v-for="skill in skills" :key="skill.key" class="block text-sm font-semibold text-[var(--ink2)]">
              {{ skill.label }}
              <input
                v-model.number="manual[skill.key]"
                type="number"
                min="0"
                max="9"
                step="0.5"
                class="ct-input mt-1 w-full"
                required
              />
            </label>
          </div>
          <div class="flex flex-wrap justify-end gap-2">
            <button type="button" class="ct-btn" :disabled="placement.loading" @click="mode = 'choice'">Back</button>
            <button type="submit" class="btn btn-primary" :disabled="placement.loading">
              {{ placement.loading ? 'Saving...' : 'Save starting bands' }}
            </button>
          </div>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listFullExamSets } from '@/services/fullExamService.js'
import { useAuthStore } from '@/stores/auth.js'
import { useFullExamStore } from '@/stores/fullExam.js'
import { usePlacementStore } from '@/stores/placement.js'
import { stageRoute } from '@/utils/fullExamNav.js'

const emit = defineEmits(['completed'])
const auth = useAuthStore()
const placement = usePlacementStore()
const fullExam = useFullExamStore()
const router = useRouter()

const mode = ref('choice')
const loading = ref(false)
const error = ref('')
const manual = reactive({ reading: 5.5, listening: 5.5, writing: 5.5, speaking: 5.5 })

const skills = [
  { key: 'reading', label: 'Reading' },
  { key: 'listening', label: 'Listening' },
  { key: 'writing', label: 'Writing' },
  { key: 'speaking', label: 'Speaking' },
]

const visible = computed(() => {
  const session = fullExam.session || fullExam.getSession()
  return auth.isAuthenticated && placement.needsPlacement && !session?.placementMode
})

onMounted(async () => {
  await placement.loadStatus()
})

async function startFullPlacement() {
  loading.value = true
  error.value = ''
  try {
    const sets = await listFullExamSets(200)
    if (!sets.length) {
      error.value = 'No full mock exam set is available.'
      return
    }
    const set = sets[Math.floor(Math.random() * sets.length)]
    fullExam.start(set, { placementMode: true })
    const session = fullExam.getSession()
    router.push(stageRoute(router, session, 'reading'))
  } catch (err) {
    error.value = err.response?.data?.detail || 'Cannot start full placement test.'
  } finally {
    loading.value = false
  }
}

async function submitManual() {
  const result = await placement.submitManual({ ...manual })
  if (result) await complete()
}

async function complete() {
  await auth.fetchProfile()
  emit('completed')
}
</script>

<style scoped>
.choice-card {
  display: flex;
  min-height: 160px;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  padding: 18px;
  text-align: left;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.choice-card:hover:enabled {
  border-color: #34d399;
  transform: translateY(-1px);
}
.choice-card:disabled {
  cursor: wait;
  opacity: 0.7;
}
.choice-card__icon {
  display: inline-flex;
  height: 34px;
  width: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #111;
  color: white;
  font-size: 12px;
  font-weight: 800;
}
.choice-card__title {
  font-size: 15px;
  font-weight: 800;
  color: var(--ink);
}
.choice-card__body {
  font-size: 13px;
  line-height: 1.5;
  color: var(--ink3);
}
</style>

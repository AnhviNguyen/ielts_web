<template>
  <div class="space-y-4">
    <AlertBanner :alerts="alerts" />

    <NextWeekForecast />

    <div class="ct-card p-5" data-tour="forecast-chart">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="text-sm font-bold text-[var(--ink)]">Dự báo điểm IELTS</div>
          <p class="text-[11px] text-[var(--ink3)]">
            NeuralProphet · {{ forecast?.sample_days ?? 0 }} ngày dữ liệu
            <span v-if="forecast?.trainer" class="ml-1">· {{ trainerLabel }}</span>
          </p>
        </div>
        <div class="flex flex-wrap gap-2" data-tour="forecast-skills">
          <button
            v-for="s in skillOptions"
            :key="s.id"
            class="rounded-lg px-3 py-1.5 text-[12px] font-medium transition"
            :class="selectedSkill === s.id
              ? 'bg-[var(--spotify-green)] text-black'
              : 'border border-[var(--border)] text-[var(--ink2)] hover:bg-[var(--bg2)]'"
            @click="selectSkill(s.id)"
          >{{ s.label }}</button>
        </div>
      </div>

      <div v-if="loading" class="py-16 text-center text-[13px] text-[var(--ink3)]">Đang tải dự báo…</div>
      <div v-else-if="error" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-800">{{ error }}</div>
      <div v-else-if="forecast?.cold_start" class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-6 text-center">
        <p class="text-[13px] font-medium text-amber-900">Chưa đủ dữ liệu lịch sử</p>
        <p class="mt-1 text-[12px] text-amber-800">Cần ít nhất 14 ngày luyện tập để dự báo chính xác. Hãy hoàn thành thêm bài practice.</p>
      </div>
      <ScoreChart
        v-else
        :history="forecast?.history || []"
        :forecast="forecast?.forecast || []"
        :target="targetBand"
      />

      <div v-if="forecast && !forecast.cold_start" class="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--border)] pt-4 sm:grid-cols-4">
        <div class="rounded-lg bg-[var(--bg)] px-3 py-2">
          <div class="text-[10px] text-[var(--ink3)]">MAE</div>
          <div class="text-[14px] font-bold text-[var(--ink)]">{{ forecast.mae?.toFixed(2) ?? '—' }}</div>
        </div>
        <div class="rounded-lg bg-[var(--bg)] px-3 py-2">
          <div class="text-[10px] text-[var(--ink3)]">RMSE</div>
          <div class="text-[14px] font-bold text-[var(--ink)]">{{ forecast.rmse?.toFixed(2) ?? '—' }}</div>
        </div>
        <div class="rounded-lg bg-[var(--bg)] px-3 py-2">
          <div class="text-[10px] text-[var(--ink3)]">Dự báo +14 ngày</div>
          <div class="text-[14px] font-bold text-[var(--spotify-green)]">{{ endForecast ?? '—' }}</div>
        </div>
        <div class="rounded-lg bg-[var(--bg)] px-3 py-2">
          <div class="text-[10px] text-[var(--ink3)]">Mục tiêu</div>
          <div class="text-[14px] font-bold text-[var(--ink)]">{{ targetBand }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import { fetchForecast, fetchForecastAlerts } from '@/services/forecastService.js'
import ScoreChart from '@/components/dashboard/ScoreChart.vue'
import AlertBanner from '@/components/dashboard/AlertBanner.vue'
import NextWeekForecast from '@/components/dashboard/NextWeekForecast.vue'

const auth = useAuthStore()

const skillOptions = [
  { id: 'overall', label: 'Overall' },
  { id: 'reading', label: 'Reading' },
  { id: 'listening', label: 'Listening' },
  { id: 'writing', label: 'Writing' },
  { id: 'speaking', label: 'Speaking' },
]

const selectedSkill = ref('overall')
const forecast = ref(null)
const alerts = ref([])
const alertTarget = ref(7)
const loading = ref(false)
const error = ref('')

const targetBand = computed(() => Number(auth.profile?.target_band || alertTarget.value || 7))

const trainerLabel = computed(() => {
  const t = forecast.value?.trainer
  if (t === 'neuralprophet') return 'NeuralProphet'
  if (t === 'linear_seasonal') return 'Linear + mùa tuần'
  if (t === 'cold_start') return 'Cold start'
  return t || '—'
})

const endForecast = computed(() => {
  const last = forecast.value?.forecast?.at(-1)
  return last ? `${last.yhat.toFixed(1)} (${last.yhat_lower.toFixed(1)}–${last.yhat_upper.toFixed(1)})` : null
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [fc, al] = await Promise.all([
      fetchForecast(selectedSkill.value),
      fetchForecastAlerts(),
    ])
    forecast.value = fc
    alerts.value = al?.alerts || []
    alertTarget.value = al?.target_band ?? targetBand.value
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Không tải được dự báo'
    forecast.value = null
  } finally {
    loading.value = false
  }
}

function selectSkill(id) {
  selectedSkill.value = id
}

watch(selectedSkill, () => load())
onMounted(load)
</script>

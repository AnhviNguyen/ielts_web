<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-[#0f0f1a] px-6 text-white">
    <div class="w-full max-w-md text-center">
      <div class="text-[11px] font-bold uppercase tracking-widest text-[#34d399]">Full Mock Exam</div>
      <h1 class="mt-2 text-2xl font-bold">{{ title }}</h1>
      <p class="mt-3 text-[14px] text-white/70">{{ message }}</p>

      <div v-if="lastResult" class="mt-6 rounded-xl border border-white/10 bg-white/5 p-4 text-left text-[13px]">
        <div class="font-semibold text-[#34d399]">Kết quả vừa xong</div>
        <div class="mt-2 text-white/80">{{ lastResult }}</div>
      </div>

      <div class="mt-8">
        <div class="text-[12px] text-white/50">Nghỉ giữa các phần (tùy chọn)</div>
        <div class="mt-2 font-mono text-4xl font-bold tabular-nums">{{ fmtBreak }}</div>
      </div>

      <button
        type="button"
        class="mt-8 w-full rounded-xl bg-[#34d399] px-6 py-3 text-[15px] font-semibold text-[#0f0f1a] hover:bg-[#2dd4a0]"
        @click="continueNext"
      >
        {{ breakRemaining > 0 ? 'Bỏ qua & tiếp tục →' : `Bắt đầu ${nextLabel} →` }}
      </button>

      <p class="mt-4 text-[11px] text-white/40">
        Lưu ý: Thi thật không có nghỉ giữa Reading và Listening — đây là thời gian nghỉ luyện tập.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFullExamStore } from '@/stores/fullExam.js'
import { nextStage, stageRoute } from '@/utils/fullExamNav.js'

const BREAK_SECONDS = 120

const STAGE_LABELS = {
  reading: 'Reading',
  listening: 'Listening',
  writing: 'Writing',
  speaking: 'Speaking',
}

const route = useRoute()
const router = useRouter()
const fullExam = useFullExamStore()

const afterStage = computed(() => route.query.after || '')
const breakRemaining = ref(BREAK_SECONDS)
let timerId = null

const session = computed(() => fullExam.getSession())

const nxt = computed(() => nextStage(afterStage.value))

const nextLabel = computed(() => STAGE_LABELS[nxt.value] || nxt.value)

const title = computed(() => {
  const done = STAGE_LABELS[afterStage.value] || afterStage.value
  return `Hoàn thành ${done}`
})

const message = computed(() => {
  if (!nxt.value) return 'Chuẩn bị xem tổng kết.'
  return `Tiếp theo: ${nextLabel.value}. Bạn có thể nghỉ tối đa 2 phút trước khi bắt đầu.`
})

const lastResult = computed(() => {
  const r = session.value?.results?.[afterStage.value]
  if (!r) return ''
  if (r.band != null) return `Band ước tính: ${r.band}`
  if (r.estimatedBand != null) return `Band ước tính: ${r.estimatedBand}`
  if (r.correct != null) return `Đúng ${r.correct}/${r.total}`
  if (r.summary?.band_estimate != null) return `Speaking band: ${r.summary.band_estimate}`
  return ''
})

const fmtBreak = computed(() => {
  const s = breakRemaining.value
  const m = String(Math.floor(s / 60)).padStart(2, '0')
  const ss = String(s % 60).padStart(2, '0')
  return `${m}:${ss}`
})

function continueNext() {
  const sess = session.value
  if (!sess) {
    router.replace('/full-exam')
    return
  }
  const next = nxt.value
  if (!next) {
    fullExam.setStage('done')
    router.push(stageRoute(router, sess, 'done'))
    return
  }
  fullExam.setStage(next)
  router.push(stageRoute(router, sess, next))
}

onMounted(() => {
  if (!session.value || route.query.session !== session.value.sessionId || !afterStage.value) {
    router.replace('/full-exam')
    return
  }
  timerId = setInterval(() => {
    if (breakRemaining.value > 0) breakRemaining.value--
  }, 1000)
})

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>

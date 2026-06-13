<template>
  <div class="min-h-screen bg-[var(--bg)]">
    <div class="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--bg)]/95 px-6 py-3 backdrop-blur">
      <div class="mx-auto flex max-w-5xl items-center justify-between">
        <button
          class="flex items-center gap-1.5 text-sm text-[var(--ink2)] transition hover:text-[var(--ink)]"
          @click="router.push('/writing/ielts')"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          Quay lại
        </button>
        <div class="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          <span class="text-sm font-semibold text-[var(--ink)]">Kết quả Writing</span>
        </div>
        <RouterLink to="/writing/ielts" class="ct-btn text-[12px]">Luyện bài mới</RouterLink>
      </div>
    </div>

    <div v-if="loading" class="flex h-64 items-center justify-center">
      <div class="flex flex-col items-center gap-3">
        <div class="h-8 w-8 animate-spin rounded-full border-2 border-[#34d399] border-t-transparent"/>
        <p class="text-sm text-[var(--ink2)]">Đang tải phản hồi AI…</p>
      </div>
    </div>

    <div v-else-if="error" class="mx-auto mt-16 max-w-md rounded-xl border border-[#f43f5e44] bg-[#f43f5e08] p-8 text-center">
      <p class="text-sm text-[#f43f5e]">{{ error }}</p>
      <button class="ct-btn mt-4" @click="router.back()">Quay lại</button>
    </div>

    <div v-else-if="data" class="mx-auto max-w-5xl space-y-5 px-4 py-6">
      <!-- Header -->
      <div class="card p-5">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div class="text-[11px] uppercase tracking-wider text-[var(--ink3)]">
              Task {{ data.task_type || 2 }}
              <span v-if="task1Result"> · Bộ đề đầy đủ</span>
              · {{ data.word_count || 0 }} từ
            </div>
            <h1 class="mt-1 text-lg text-[var(--ink)]">{{ data.setTitle || data.title || 'IELTS Writing' }}</h1>
            <p v-if="evalData.summary" class="mt-2 text-sm font-normal leading-relaxed text-[var(--ink2)]">{{ evalData.summary }}</p>
          </div>
          <BandScoreRing :band="Number(data.band_score || evalData.overall_band || 0)" />
        </div>
        <p v-if="evalData.word_count_comment" class="mt-3 text-[12px] font-normal text-[var(--ink3)]">{{ evalData.word_count_comment }}</p>
      </div>

      <!-- Combined Task 1 + Task 2 summary -->
      <div v-if="task1Result || data.task_type === 2" class="card overflow-hidden p-0">
        <div class="border-b border-[var(--border)] bg-[var(--bg-interactive)] px-5 py-3.5">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--ink)]">Tổng kết bộ đề Writing</div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[520px] text-left text-sm">
            <thead>
              <tr class="border-b border-[var(--border)] text-[11px] uppercase tracking-wider text-[var(--ink3)]">
                <th class="px-5 py-3">Task</th>
                <th class="px-5 py-3">Band</th>
                <th class="px-5 py-3">Số từ</th>
                <th class="px-5 py-3">Tiêu chí (TA/CC/LR/GRA)</th>
                <th class="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="task1Result" class="border-b border-[var(--border)]">
                <td class="px-5 py-3 font-semibold text-[var(--ink)]">Task 1</td>
                <td class="px-5 py-3 tabular-nums text-[var(--spotify-green-dark)]">{{ Number(task1Result.band_score || 0).toFixed(1) }}</td>
                <td class="px-5 py-3 text-[var(--ink2)]">{{ task1Result.word_count || 0 }}</td>
                <td class="px-5 py-3 text-[12px] text-[var(--ink3)]">{{ task1CriteriaLabel }}</td>
                <td class="px-5 py-3">
                  <RouterLink
                    v-if="task1Result.history_id"
                    :to="{ name: 'WritingResult', params: { historyId: task1Result.history_id } }"
                    class="text-[12px] text-[var(--spotify-green-dark)] hover:underline"
                  >Chi tiết</RouterLink>
                </td>
              </tr>
              <tr>
                <td class="px-5 py-3 font-semibold text-[var(--ink)]">Task {{ data.task_type || 2 }}</td>
                <td class="px-5 py-3 tabular-nums text-[var(--spotify-green-dark)]">{{ Number(data.band_score || evalData.overall_band || 0).toFixed(1) }}</td>
                <td class="px-5 py-3 text-[var(--ink2)]">{{ data.word_count || 0 }}</td>
                <td class="px-5 py-3 text-[12px] text-[var(--ink3)]">{{ task2CriteriaLabel }}</td>
                <td class="px-5 py-3 text-[12px] text-[var(--ink3)]">Đang xem</td>
              </tr>
              <tr v-if="task1Result" class="bg-[var(--bg-interactive)] font-semibold">
                <td class="px-5 py-3 text-[var(--ink)]">Trung bình</td>
                <td class="px-5 py-3 tabular-nums text-[var(--ink)]">{{ combinedBand }}</td>
                <td class="px-5 py-3 text-[var(--ink2)]">{{ (task1Result.word_count || 0) + (data.word_count || 0) }}</td>
                <td class="px-5 py-3" colspan="2"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Task 1 recap removed — merged into table above -->

      <!-- Annotated essay -->
      <div v-if="data.essay_text" class="card p-5">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div class="text-xs uppercase tracking-wider text-[var(--ink2)]">Bài viết của bạn</div>
          <div v-if="hasMarks" class="flex flex-wrap gap-3 text-[11px] text-[var(--ink3)]">
            <span class="inline-flex items-center gap-1.5">
              <span class="inline-block h-2.5 w-2.5 rounded-sm bg-rose-200 ring-1 ring-rose-300"></span>
              Lỗi ngữ pháp
            </span>
            <span class="inline-flex items-center gap-1.5">
              <span class="inline-block h-2.5 w-2.5 rounded-sm bg-amber-200 ring-1 ring-amber-300"></span>
              Từ vựng yếu
            </span>
          </div>
        </div>
        <div
          class="writing-annotated-essay whitespace-pre-wrap text-sm font-normal leading-relaxed text-[var(--ink)]"
          v-html="annotatedEssayHtml"
        />
        <p v-if="!hasMarks" class="mt-2 text-[12px] font-normal text-[var(--ink3)]">
          Không tìm thấy cụm cần đánh dấu trực tiếp — xem chi tiết ở các mục bên dưới.
        </p>
      </div>

      <!-- 4 criteria -->
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div v-for="c in criteria" :key="c.key" class="card p-4 text-center">
          <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--ink3)]">{{ c.label }}</div>
          <div class="mt-1 text-2xl font-bold" :style="{ color: scoreColor(c.value) }">{{ c.value.toFixed(1) }}</div>
          <div class="text-[10px] text-[var(--ink3)]">/ 9</div>
        </div>
      </div>

      <!-- Strengths & improvements -->
      <div class="grid gap-4 md:grid-cols-2">
        <div class="card p-4">
          <div class="mb-3 text-xs uppercase tracking-wider text-[#34d399]">Điểm mạnh</div>
          <ul class="space-y-2 text-sm font-normal text-[var(--ink2)]">
            <li v-for="(s, i) in evalData.strengths || []" :key="i" class="flex gap-2">
              <span class="text-[#34d399]">✓</span><span>{{ s }}</span>
            </li>
          </ul>
        </div>
        <div class="card p-4">
          <div class="mb-3 text-xs uppercase tracking-wider text-amber-600">Cần cải thiện</div>
          <ul class="space-y-2 text-sm font-normal text-[var(--ink2)]">
            <li v-for="(s, i) in evalData.improvements || []" :key="i" class="flex gap-2">
              <span class="text-amber-500">→</span><span>{{ s }}</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Grammar -->
      <div class="card p-5">
        <div class="mb-4 flex items-center justify-between">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Ngữ pháp (GRA)</div>
          <span class="rounded-full bg-[var(--bg)] px-2.5 py-0.5 text-sm font-bold text-[var(--ink)]">
            {{ Number(grammar.band || evalData.grammar_accuracy || 0).toFixed(1) }}/9
          </span>
        </div>
        <div v-if="grammar.errors?.length" class="space-y-3">
          <div
            v-for="(err, i) in grammar.errors"
            :key="i"
            class="rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3 text-sm"
          >
            <div class="flex flex-wrap items-center gap-2">
              <span class="rounded bg-rose-50 px-2 py-0.5 text-rose-700 line-through">{{ err.original }}</span>
              <span class="text-[var(--ink3)]">→</span>
              <span class="rounded bg-emerald-50 px-2 py-0.5 text-emerald-800">{{ err.correction }}</span>
              <span
                class="rounded-full px-2 py-0.5 text-[10px] uppercase"
                :class="err.severity === 'major' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'"
              >{{ err.severity === 'major' ? 'Nghiêm trọng' : 'Nhẹ' }}</span>
            </div>
            <p v-if="err.rule" class="mt-2 text-[12px] text-[var(--ink3)]">{{ err.rule }}</p>
          </div>
        </div>
        <p v-else class="text-sm text-[var(--ink3)]">Không phát hiện lỗi ngữ pháp cụ thể.</p>
        <ul v-if="grammar.tips?.length" class="mt-4 space-y-1 text-[12px] text-[var(--ink2)]">
          <li v-for="(t, i) in grammar.tips" :key="i">• {{ t }}</li>
        </ul>
      </div>

      <!-- Vocabulary -->
      <div class="card p-5">
        <div class="mb-4 flex items-center justify-between">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Từ vựng (LR)</div>
          <span class="rounded-full bg-[var(--bg)] px-2.5 py-0.5 text-sm font-bold text-[var(--ink)]">
            {{ Number(vocab.band || evalData.lexical_resource || 0).toFixed(1) }}/9
          </span>
        </div>
        <div v-if="vocab.weak_words?.length" class="space-y-2">
          <div
            v-for="(w, i) in vocab.weak_words"
            :key="i"
            class="flex flex-wrap items-baseline gap-2 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
          >
            <span class="text-[var(--ink)]">{{ w.word }}</span>
            <span class="text-[var(--ink3)]">→</span>
            <span class="text-[#34d399]">{{ w.better }}</span>
            <span v-if="w.reason" class="w-full text-[12px] text-[var(--ink3)]">{{ w.reason }}</span>
          </div>
        </div>
        <ul v-if="vocab.upgrades?.length" class="mt-3 space-y-1 text-[12px] text-[var(--ink2)]">
          <li v-for="(u, i) in vocab.upgrades" :key="i">↑ {{ u }}</li>
        </ul>
        <ul v-if="vocab.tips?.length" class="mt-3 space-y-1 text-[12px] text-[var(--ink3)]">
          <li v-for="(t, i) in vocab.tips" :key="i">• {{ t }}</li>
        </ul>
      </div>

      <!-- Paragraph allocation -->
      <div class="card p-5">
        <div class="mb-4 flex items-center justify-between">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--ink2)]">Phân bổ đoạn văn</div>
          <span
            class="rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
            :class="allocation.structure_ok ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
          >
            {{ allocation.structure_ok ? 'Cấu trúc ổn' : 'Cần điều chỉnh' }}
          </span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[480px] text-left text-sm">
            <thead>
              <tr class="border-b border-[var(--border)] text-[11px] uppercase tracking-wider text-[var(--ink3)]">
                <th class="pb-2 pr-4">Đoạn</th>
                <th class="pb-2 pr-4">Mục tiêu</th>
                <th class="pb-2 pr-4">Bạn viết</th>
                <th class="pb-2">Nhận xét</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(sec, i) in allocation.sections || []"
                :key="i"
                class="border-b border-[var(--border)] last:border-0"
              >
                <td class="py-2.5 pr-4 text-[var(--ink)]">{{ sec.name }}</td>
                <td class="py-2.5 pr-4 text-[var(--ink2)]">{{ sec.recommended_words }}</td>
                <td class="py-2.5 pr-4 tabular-nums text-[var(--ink)]">{{ sec.your_words ?? '—' }}</td>
                <td class="py-2.5 text-[12px] text-[var(--ink3)]">{{ sec.feedback }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <ul v-if="allocation.tips?.length" class="mt-4 space-y-1 text-[12px] text-[var(--ink2)]">
          <li v-for="(t, i) in allocation.tips" :key="i">• {{ t }}</li>
        </ul>
      </div>

      <!-- Model paragraph -->
      <div v-if="modelParagraph.improved_text || modelParagraph.explanation" class="card overflow-hidden p-0">
        <div class="border-b border-[var(--border)] bg-[var(--bg-interactive)] px-5 py-4">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--spotify-green-dark)]">Đoạn văn mẫu nâng band</div>
          <p v-if="modelParagraph.focus" class="mt-1 text-sm text-[var(--ink2)]">{{ modelParagraph.focus }}</p>
        </div>
        <div class="space-y-4 p-5">
          <div v-if="modelParagraph.weak_excerpt">
            <div class="mb-1 text-[11px] uppercase text-[var(--ink3)]">Đoạn gốc (cần cải thiện)</div>
            <p class="rounded-lg border border-[var(--border)] bg-[var(--bg-interactive)] p-3 text-sm font-normal italic text-[var(--ink2)]">{{ modelParagraph.weak_excerpt }}</p>
          </div>
          <div v-if="modelParagraph.improved_text">
            <div class="mb-1 text-[11px] uppercase text-[var(--spotify-green-dark)]">Phiên bản nâng band</div>
            <p class="rounded-lg border border-[var(--spotify-green)]/40 bg-[var(--green-bg)] p-3 text-sm font-normal leading-relaxed text-[var(--ink)]">{{ modelParagraph.improved_text }}</p>
          </div>
          <p v-if="modelParagraph.explanation" class="text-sm font-normal text-[var(--ink2)]">{{ modelParagraph.explanation }}</p>
          <p v-if="modelParagraph.expected_band_gain" class="text-[12px] text-[#34d399]">
            {{ modelParagraph.expected_band_gain }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BandScoreRing from '@/components/speaking/BandScoreRing.vue'
import { fetchWritingResult } from '@/services/writingService.js'
import { buildAnnotatedEssayHtml } from '@/utils/writingAnnotations.js'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const data = ref(null)
const task1Result = ref(null)

const evalData = computed(() => data.value?.evaluation || {})
const grammar = computed(() => evalData.value.grammar || {})
const vocab = computed(() => evalData.value.vocabulary || {})
const allocation = computed(() => evalData.value.paragraph_allocation || {})
const modelParagraph = computed(() => evalData.value.model_paragraph || {})

const annotatedEssayHtml = computed(() =>
  buildAnnotatedEssayHtml(
    data.value?.essay_text,
    grammar.value.errors,
    vocab.value.weak_words,
  ),
)

const hasMarks = computed(() =>
  annotatedEssayHtml.value.includes('writing-mark'),
)

const criteria = computed(() => {
  const e = evalData.value
  return [
    { key: 'ta', label: 'Task', value: Number(e.task_achievement || 0) },
    { key: 'cc', label: 'Coherence', value: Number(e.coherence_cohesion || 0) },
    { key: 'lr', label: 'Lexical', value: Number(e.lexical_resource || 0) },
    { key: 'gra', label: 'Grammar', value: Number(e.grammar_accuracy || 0) },
  ]
})

function formatCriteria(e) {
  if (!e) return '—'
  const parts = [
    Number(e.task_achievement || 0).toFixed(1),
    Number(e.coherence_cohesion || 0).toFixed(1),
    Number(e.lexical_resource || 0).toFixed(1),
    Number(e.grammar_accuracy || 0).toFixed(1),
  ]
  return parts.join(' / ')
}

const task1CriteriaLabel = computed(() => formatCriteria(task1Result.value?.evaluation))
const task2CriteriaLabel = computed(() => formatCriteria(evalData.value))

const combinedBand = computed(() => {
  if (!task1Result.value) return ''
  const t1 = Number(task1Result.value.band_score || 0)
  const t2 = Number(data.value?.band_score || evalData.value.overall_band || 0)
  return ((t1 + t2) / 2).toFixed(1)
})

function scoreColor(score) {
  if (score >= 7.5) return '#34d399'
  if (score >= 6) return '#f59e0b'
  return '#f43f5e'
}

function applyState(state) {
  if (!state?.evaluation) return false
  task1Result.value = state.task1Result || null
  data.value = {
    history_id: state.history_id,
    band_score: state.band ?? state.band_score,
    task_type: state.task_type,
    word_count: state.word_count,
    essay_text: state.essay_text || '',
    title: state.title || 'IELTS Writing',
    setTitle: state.setTitle,
    evaluation: state.evaluation,
  }
  return true
}

async function load() {
  const state = history.state?.writingResult
  if (applyState(state)) return

  const historyId = route.params.historyId
  if (!historyId) {
    error.value = 'Không có dữ liệu kết quả.'
    return
  }

  loading.value = true
  try {
    data.value = await fetchWritingResult(historyId)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Không thể tải kết quả Writing.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
:deep(.writing-mark) {
  border-radius: 2px;
  padding: 0 1px;
  font-weight: inherit;
  cursor: help;
}
:deep(.writing-mark--grammar) {
  background: var(--rose-bg);
  color: var(--rose);
  text-decoration: line-through;
  text-decoration-color: color-mix(in srgb, var(--rose) 70%, transparent);
}
:deep(.writing-mark--vocab) {
  background: var(--amber-bg, rgb(254 243 199));
  color: var(--amber);
  border-bottom: 2px solid var(--amber);
}
.writing-annotated-essay {
  font-weight: 400;
}
</style>

<!--
  MatchingSet.vue
  ──────────────
  Drag-and-drop matching component for question set types:
    MATCHING_HEADINGS  — drag roman-numeral headings to paragraph slots
    MATCHING_FEATURES  — drag researcher/option names to statement slots
    MATCHING_ENDINGS   — drag sentence endings to beginning slots

  Architecture (SOLID):
  - Single Responsibility: only handles drag-drop matching UI
  - Open/Closed: new match types work via props, no code change
  - Dependency: uses sanitizeQuizHtml for description HTML
-->
<template>
  <div
    class="card p-4"
    :class="isCurrent ? 'ring-2 ring-[rgba(124,106,247,0.35)]' : ''"
  >
    <!-- Header -->
    <div class="mb-1 text-xs font-semibold text-[var(--ink2)]">{{ title }}</div>
    <div
      v-if="description"
      class="mb-4 text-sm leading-relaxed text-[var(--ink2)]"
      v-html="sanitizeQuizHtml(description)"
    />

    <!-- Options pool (drag source) -->
    <div
      class="mb-4 min-h-[44px] flex flex-wrap gap-2 rounded-xl border border-[var(--border2)] bg-[var(--bg)] p-3"
      @dragover.prevent
      @drop.stop="onDropToPool($event)"
      @dragenter.prevent
    >
      <span
        v-if="!poolOptions.length"
        class="text-[11px] italic text-[var(--ink3)]"
      >All options placed</span>
      <div
        v-for="opt in poolOptions"
        :key="opt.option"
        draggable="true"
        class="matching-chip cursor-grab select-none rounded-lg border border-[var(--border2)] bg-white px-2.5 py-1.5 text-xs font-medium shadow-sm transition-all hover:border-[#34d399] hover:shadow-md active:scale-95 active:opacity-70"
        :class="dragging === opt.option ? 'opacity-30 scale-95' : ''"
        @dragstart="onDragFromPool($event, opt.option)"
        @dragend="dragging = null"
      >
        <span class="mr-1 font-bold text-[#34d399]">{{ opt.option }}</span>
        <span class="text-[var(--ink)]">{{ opt.text }}</span>
      </div>
    </div>

    <!-- Question rows with drop zones -->
    <div class="space-y-2">
      <div
        v-for="q in sortedQuestions"
        :key="q.id"
        class="flex flex-wrap items-center gap-2 rounded-xl border px-3 py-2.5 transition-all"
        :class="[
          dragTarget === q.id
            ? 'border-[#34d399] bg-[#f0fdf4]'
            : 'border-[var(--border2)] bg-[var(--surface)]',
        ]"
        @dragover.prevent
        @dragenter.prevent="dragTarget = q.id"
        @dragleave="onDragLeave($event, q.id)"
        @drop.stop="onDropToQuestion($event, q.id)"
      >
        <!-- Order badge -->
        <div
          class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--bg2)] text-[11px] font-bold text-[var(--ink2)]"
        >
          {{ q.order }}
        </div>

        <!-- Statement / paragraph label -->
        <div class="min-w-0 flex-1 text-sm leading-snug text-[var(--ink)]">
          {{ q.text }}
        </div>

        <!-- Placed chip or empty drop-zone -->
        <div class="flex shrink-0 flex-wrap items-center gap-1">
          <template v-if="localAnswers[q.id]">
            <!-- Placed chip — also draggable -->
            <div
              draggable="true"
              class="flex cursor-grab items-center gap-1.5 rounded-lg border border-[#34d399] bg-[#f0fdf4] px-2.5 py-1 text-xs font-semibold text-[#059669] select-none active:scale-95"
              @dragstart="onDragFromQuestion($event, q.id)"
              @dragend="dragging = null"
            >
              <span class="font-bold">{{ localAnswers[q.id] }}</span>
              <span class="text-[var(--ink3)] whitespace-normal">
                {{ optionText(localAnswers[q.id]) }}
              </span>
            </div>
            <!-- Clear button -->
            <button
              class="flex h-5 w-5 items-center justify-center rounded-full transition-colors hover:bg-[var(--bg2)]"
              title="Remove answer"
              @click.stop="clearAnswer(q.id)"
            >
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </template>

          <!-- Empty drop zone -->
          <div
            v-else
            class="rounded-lg border border-dashed border-[var(--border2)] px-4 py-1.5 text-[11px] italic text-[var(--ink3)]"
          >
            Drop here
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { sanitizeQuizHtml } from '@/utils/sanitizeHtml.js'

// ── Props ──────────────────────────────────────────────────────────────────────
const props = defineProps({
  title:       { type: String,  default: '' },
  description: { type: String,  default: '' },
  /** [{option: 'i', text: 'A fresh goal'}, ...] */
  options:     { type: Array,   default: () => [] },
  /** [{id, order, sort, text}, ...] */
  questions:   { type: Array,   default: () => [] },
  /** {questionId: optionKey, ...} — from store */
  answers:     { type: Object,  default: () => ({}) },
  allowReuse:  { type: Boolean, default: false },
  isCurrent:   { type: Boolean, default: false },
})

const emit = defineEmits(['answer'])

// ── Local answer state (for instant drag feedback) ────────────────────────────
const localAnswers = ref({ ...props.answers })
watch(
  () => props.answers,
  (v) => { localAnswers.value = { ...v } },
  { deep: true },
)

// ── Sorted questions ─────────────────────────────────────────────────────────
const sortedQuestions = computed(() =>
  [...props.questions].sort((a, b) => (a.order ?? a.sort ?? 0) - (b.order ?? b.sort ?? 0)),
)

// ── Options pool: exclude already-placed options when allowReuse is false ─────
const poolOptions = computed(() => {
  if (props.allowReuse) return props.options
  const placed = new Set(Object.values(localAnswers.value).filter(Boolean))
  return props.options.filter((o) => !placed.has(o.option))
})

function optionText(optionKey) {
  return props.options.find((o) => o.option === optionKey)?.text ?? ''
}

// ── Drag state ────────────────────────────────────────────────────────────────
const dragging = ref(null)       // option key currently being dragged
const draggingFrom = ref(null)   // question id if chip came from a placed slot
const dragTarget = ref(null)     // question id currently hovered

function onDragFromPool(event, optionKey) {
  dragging.value = optionKey
  draggingFrom.value = null
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', optionKey)
}

function onDragFromQuestion(event, questionId) {
  const optKey = localAnswers.value[questionId]
  if (!optKey) return
  dragging.value = optKey
  draggingFrom.value = questionId
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', optKey)
}

function onDragLeave(event, questionId) {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    if (dragTarget.value === questionId) dragTarget.value = null
  }
}

// Drop onto a question row ──────────────────────────────────────────────────────
function onDropToQuestion(event, targetQuestionId) {
  dragTarget.value = null
  const optKey = event.dataTransfer.getData('text/plain') || dragging.value
  if (!optKey) return

  // If dragged FROM another question slot → clear source
  if (draggingFrom.value && draggingFrom.value !== targetQuestionId) {
    localAnswers.value[draggingFrom.value] = null
    emit('answer', { questionId: draggingFrom.value, value: '' })
  }

  // If target already has an answer (swap case), it returns to pool automatically
  localAnswers.value[targetQuestionId] = optKey
  dragging.value = null
  draggingFrom.value = null
  emit('answer', { questionId: targetQuestionId, value: optKey })
}

// Drop back onto the pool ──────────────────────────────────────────────────────
function onDropToPool(event) {
  dragTarget.value = null
  if (!draggingFrom.value) return  // was from pool → no-op
  localAnswers.value[draggingFrom.value] = null
  emit('answer', { questionId: draggingFrom.value, value: '' })
  dragging.value = null
  draggingFrom.value = null
}

function clearAnswer(questionId) {
  localAnswers.value[questionId] = null
  emit('answer', { questionId, value: '' })
}
</script>

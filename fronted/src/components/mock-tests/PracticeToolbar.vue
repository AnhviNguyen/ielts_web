<template>
  <div class="fixed left-4 top-1/2 z-[150] -translate-y-1/2 flex flex-col gap-2" v-if="practiceMode">
    <!-- Highlight tool -->
    <div class="relative">
      <button
        class="group flex h-11 w-11 items-center justify-center rounded-xl border shadow-md transition-all hover:-translate-x-0.5 hover:shadow-lg"
        :class="activeTool === 'highlight' ? 'border-[#fde047] bg-[#fef9c3] text-[#854d0e]' : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-[#fde047] hover:bg-[#fefce8]'"
        title="Tô màu (H)"
        @click="toggleTool('highlight')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 11-6 6v3h9l3-3"/>
          <path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/>
        </svg>
      </button>

      <!-- Highlight color picker -->
      <div v-if="activeTool === 'highlight'" class="absolute left-14 top-0 flex gap-1.5 rounded-xl border border-[var(--border)] bg-white p-1.5 shadow-lg">
        <button v-for="c in colors" :key="c.value" :title="c.label"
          class="h-6 w-6 rounded-lg border-2 transition-transform hover:scale-110"
          :class="highlightColor === c.value ? 'border-[var(--ink)]' : 'border-transparent'"
          :style="{ background: c.bg }"
          @click="highlightColor = c.value"
        ></button>
      </div>
    </div>

    <!-- Note tool -->
    <button
      class="flex h-11 w-11 items-center justify-center rounded-xl border shadow-md transition-all hover:-translate-x-0.5 hover:shadow-lg"
      :class="activeTool === 'note' ? 'border-[var(--blue-l)] bg-[var(--blue-bg)] text-[var(--blue)]' : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-[var(--blue-l)] hover:bg-[var(--blue-bg)]'"
      title="Ghi chú (N)"
      @click="toggleTool('note')"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
      </svg>
    </button>

    <!-- Vocabulary lookup tool -->
    <button
      class="flex h-11 w-11 items-center justify-center rounded-xl border shadow-md transition-all hover:-translate-x-0.5 hover:shadow-lg"
      :class="activeTool === 'vocab' ? 'border-[var(--violet-l)] bg-[var(--violet-bg)] text-[var(--violet)]' : 'border-[var(--border)] bg-white text-[var(--ink2)] hover:border-[var(--violet-l)] hover:bg-[var(--violet-bg)]'"
      title="Tra từ vựng (T)"
      @click="toggleTool('vocab')"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    </button>

    <!-- Divider -->
    <div class="mx-auto h-px w-8 bg-[var(--border)]"></div>

    <!-- Instructions -->
    <div class="flex h-11 w-11 items-center justify-center text-[10px] text-[var(--ink3)] leading-tight text-center">
      Công<br>cụ
    </div>
  </div>

  <!-- Note panel -->
  <Teleport to="body">
    <Transition name="slide-right">
      <div v-if="activeTool === 'note' && practiceMode" class="fixed right-0 top-0 z-[160] flex h-full w-80 flex-col bg-white shadow-2xl border-l border-[var(--border)]">
        <div class="flex shrink-0 items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <div class="flex items-center gap-2 text-sm font-semibold text-[var(--ink)]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Ghi chú
          </div>
          <button class="text-[var(--ink3)] hover:text-[var(--ink)]" @click="activeTool = null">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <textarea
          v-model="noteText"
          class="flex-1 resize-none p-4 text-[13px] text-[var(--ink)] outline-none leading-relaxed"
          placeholder="Ghi chú của bạn tại đây..."
        ></textarea>
      </div>
    </Transition>

    <!-- Vocabulary lookup panel -->
    <Transition name="slide-right">
      <div v-if="activeTool === 'vocab' && practiceMode" class="fixed right-0 top-0 z-[160] flex h-full w-80 flex-col bg-white shadow-2xl border-l border-[var(--border)]">
        <div class="flex shrink-0 items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <div class="flex items-center gap-2 text-sm font-semibold text-[var(--ink)]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            Tra từ vựng
          </div>
          <button class="text-[var(--ink3)] hover:text-[var(--ink)]" @click="activeTool = null">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="flex shrink-0 gap-2 border-b border-[var(--border)] px-4 py-3">
          <input
            v-model="vocabQuery"
            class="flex-1 rounded-xl border border-[var(--border)] px-3 py-2 text-sm outline-none focus:border-[var(--violet-l)]"
            placeholder="Nhập từ cần tra..."
            @keydown.enter="lookupVocab"
          />
          <button
            class="rounded-xl bg-[var(--violet-bg)] px-3 py-2 text-sm font-semibold text-[var(--violet)] hover:bg-[var(--violet-l)] hover:text-white transition-colors"
            @click="lookupVocab"
          >Tra</button>
        </div>
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="vocabLoading" class="text-center text-sm text-[var(--ink3)]">Đang tìm...</div>
          <div v-else-if="vocabResult" class="space-y-3">
            <div class="text-lg font-bold text-[var(--ink)]">{{ vocabResult.word }}</div>
            <div v-if="vocabResult.phonetic" class="text-sm text-[var(--ink3)]">{{ vocabResult.phonetic }}</div>
            <div v-for="(m, i) in vocabResult.meanings" :key="i" class="rounded-xl bg-[var(--bg)] p-3">
              <div class="mb-1 text-[10px] font-bold uppercase tracking-wider text-[var(--violet)]">{{ m.partOfSpeech }}</div>
              <div v-for="(def, j) in m.definitions.slice(0, 2)" :key="j" class="text-[12px] text-[var(--ink2)] leading-relaxed">{{ j + 1 }}. {{ def.definition }}</div>
              <div v-if="m.definitions[0]?.example" class="mt-1.5 rounded-lg bg-[var(--violet-bg)] px-2 py-1 text-[11px] italic text-[var(--violet)]">{{ m.definitions[0].example }}</div>
            </div>
          </div>
          <div v-else class="text-center text-sm text-[var(--ink3)]">Nhập từ và nhấn Tra để tìm kiếm.</div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

defineProps({ practiceMode: { type: Boolean, default: false } })

const activeTool    = ref(null)
const highlightColor = ref('yellow')
const noteText      = ref('')
const vocabQuery    = ref('')
const vocabResult   = ref(null)
const vocabLoading  = ref(false)

const colors = [
  { value: 'yellow', label: 'Vàng', bg: '#fef08a' },
  { value: 'green',  label: 'Xanh', bg: '#bbf7d0' },
  { value: 'rose',   label: 'Hồng', bg: '#fecdd3' },
  { value: 'blue',   label: 'Xanh dương', bg: '#bfdbfe' },
]

function toggleTool(t) {
  activeTool.value = activeTool.value === t ? null : t
}

async function lookupVocab() {
  if (!vocabQuery.value.trim()) return
  vocabLoading.value = true
  vocabResult.value  = null
  try {
    const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(vocabQuery.value.trim())}`)
    if (!res.ok) throw new Error('Not found')
    const data = await res.json()
    vocabResult.value = data[0] || null
  } catch {
    vocabResult.value = { word: vocabQuery.value, phonetic: '', meanings: [{ partOfSpeech: 'Không tìm thấy', definitions: [{ definition: 'Không có kết quả cho từ này.' }] }] }
  } finally {
    vocabLoading.value = false
  }
}
</script>

<style scoped>
.slide-right-enter-active, .slide-right-leave-active { transition: transform 0.25s ease; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }
</style>

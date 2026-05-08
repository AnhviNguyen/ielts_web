<template>
  <!-- Inline side panel — identical structure to WritingEditor's right panel -->
  <div class="flex w-80 shrink-0 flex-col overflow-hidden border-l border-[var(--border)] bg-white">

    <!-- Header -->
    <div class="flex shrink-0 items-center justify-between border-b border-[var(--border)] px-4 py-3">
      <div class="flex items-center gap-2">
        <button
          class="flex h-6 w-6 items-center justify-center rounded text-[var(--ink3)] transition hover:bg-[var(--bg2)]"
          @click="$emit('close')"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <span class="text-[12px] font-bold text-[var(--ink)]">Catbot – Personal Tutor</span>
      </div>
      <div class="flex items-center gap-1 text-[11px] text-[var(--ink3)]">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        History
      </div>
    </div>

    <!-- Messages -->
    <div ref="scrollEl" class="flex-1 space-y-3 overflow-y-auto p-4">
      <!-- Intro -->
      <div class="flex items-start gap-2">
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--bg2)] text-[10px] font-bold text-[var(--ink2)]">AI</div>
        <div class="rounded-xl rounded-tl-none bg-[var(--bg)] p-3 text-[12px] leading-relaxed text-[var(--ink)]">
          Hey! I am your personal tutor. Need help with the speaking task? Go ahead and ask.
        </div>
      </div>

      <!-- Question context chip -->
      <div v-if="questionText" class="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-[11px] text-[var(--ink2)]">
        <span class="font-semibold text-[#34d399]">Current question: </span>{{ questionText }}
      </div>

      <!-- Conversation -->
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="flex items-start gap-2"
        :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
      >
        <div
          v-if="msg.role === 'assistant'"
          class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--bg2)] text-[10px] font-bold text-[var(--ink2)]"
        >AI</div>
        <div
          class="max-w-[85%] rounded-xl p-3 text-[12px] leading-relaxed"
          :class="msg.role === 'user'
            ? 'rounded-tr-none bg-[#111] text-white'
            : 'rounded-tl-none bg-[var(--bg)] text-[var(--ink)]'"
        >
          <!-- Loading dots -->
          <span v-if="msg.loading" class="flex items-center gap-1">
            <span class="animate-bounce text-[var(--ink3)]">●</span>
            <span class="animate-bounce text-[var(--ink3)]" style="animation-delay:0.15s">●</span>
            <span class="animate-bounce text-[var(--ink3)]" style="animation-delay:0.3s">●</span>
          </span>
          <span v-else style="white-space:pre-wrap">{{ msg.text }}</span>
        </div>
      </div>
    </div>

    <!-- Quick prompts + input -->
    <div class="shrink-0 border-t border-[var(--border)] p-3">
      <div class="mb-2 flex flex-wrap gap-1.5">
        <button
          v-for="p in quickPrompts"
          :key="p"
          :disabled="loading"
          class="rounded-full border border-[var(--border2)] bg-white px-2.5 py-1 text-[10px] font-medium text-[var(--ink2)] transition-colors hover:border-[#34d399] hover:text-[#34d399] disabled:opacity-40"
          @click="callBot(p)"
        >{{ p }}</button>
      </div>
      <div class="flex gap-2">
        <input
          v-model="inputText"
          :disabled="loading"
          class="ct-input flex-1 py-1.5 text-[12px]"
          placeholder="Ask anything in your language"
          @keydown.enter.prevent="send"
        />
        <button
          :disabled="loading || !inputText.trim()"
          class="ct-btn px-3 py-1.5 text-[12px] disabled:opacity-40"
          @click="send"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M22 2L11 13"/><path d="M22 2L15 22 11 13 2 9l20-7z"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'

const props = defineProps({
  questionText: { type: String, default: '' },
})
defineEmits(['close'])

const inputText = ref('')
const loading   = ref(false)
const messages  = ref([])
const scrollEl  = ref(null)
let   msgId     = 0

const quickPrompts = [
  'How do I start?',
  'Useful Vocabulary',
  'Help with ideas',
  'Answer Guide',
  'Sample Answer',
]

async function scrollDown() {
  await nextTick()
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}

// When question changes mid-session, add a context update note
watch(() => props.questionText, (newQ, oldQ) => {
  if (newQ && newQ !== oldQ && messages.value.length > 0) {
    messages.value.push({
      id: msgId++,
      role: 'assistant',
      text: `📌 New question: "${newQ}"`,
      loading: false,
    })
    scrollDown()
  }
})

async function callBot(userText) {
  if (!userText.trim() || loading.value) return

  messages.value.push({ id: msgId++, role: 'user', text: userText, loading: false })
  const placeholder = { id: msgId++, role: 'assistant', text: '', loading: true }
  messages.value.push(placeholder)
  loading.value = true
  await scrollDown()

  try {
    const history = messages.value
      .filter(m => !m.loading && m.id < placeholder.id && !m.text.startsWith('📌'))
      .map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }))

    const res = await fetch('/api/speaking/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        question_text: props.questionText,
        user_message:  userText,
        history,
      }),
    })
    const data = await res.json()
    placeholder.loading = false
    placeholder.text    = data.reply || data.error || 'Sorry, something went wrong.'
  } catch {
    placeholder.loading = false
    placeholder.text    = 'Network error. Please try again.'
  } finally {
    loading.value = false
    await scrollDown()
  }
}

function send() {
  const t = inputText.value.trim()
  if (!t) return
  inputText.value = ''
  callBot(t)
}
</script>

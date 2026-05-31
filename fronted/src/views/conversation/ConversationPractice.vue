<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Header -->
    <header class="shrink-0 border-b border-gray-200 bg-white px-4 py-3">
      <div class="max-w-4xl mx-auto flex items-center justify-between gap-3">
        <button @click="goBack" class="text-gray-500 hover:text-gray-900 text-sm flex items-center gap-1">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
          Thoát
        </button>
        <div class="text-center min-w-0">
          <p class="font-bold text-gray-900 truncate">{{ session?.topic || 'Conversation' }}</p>
          <p class="text-xs text-gray-400">{{ session?.user_role }}</p>
        </div>
        <button
          @click="finishSession"
          :disabled="!sessionId || ending"
          class="text-sm font-semibold text-red-600 hover:text-red-700 disabled:opacity-40"
        >
          Kết thúc
        </button>
      </div>
    </header>

    <div class="flex-1 max-w-4xl mx-auto w-full flex flex-col lg:flex-row gap-0 lg:gap-4 px-4 py-4 min-h-0">

      <!-- Chat column -->
      <div class="flex-1 flex flex-col min-h-0 bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <!-- Messages -->
        <div ref="chatRef" class="flex-1 overflow-y-auto p-4 space-y-3">
          <div v-if="initLoading" class="flex justify-center py-12">
            <img src="/loading.svg" alt="" class="w-10 h-10" />
          </div>

          <template v-else>
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="flex"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <!-- User bubble -->
              <div
                v-if="msg.role === 'user'"
                class="max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed bg-gray-900 text-white rounded-br-md"
              >
                <p>{{ msg.content }}</p>
                <div v-if="msg.feedback" class="mt-2 pt-2 border-t border-white/20 text-xs space-y-1">
                  <p v-if="msg.feedback.grammar_note" class="text-amber-200">{{ msg.feedback.grammar_note }}</p>
                  <p v-if="msg.feedback.vocab_tip" class="text-emerald-200">{{ msg.feedback.vocab_tip }}</p>
                  <p v-if="msg.pronunciation?.total != null" class="text-sky-200">
                    Phát âm: {{ msg.pronunciation.total }}/10
                  </p>
                </div>
              </div>

              <!-- AI bubble -->
              <div v-else class="max-w-[85%] flex flex-col gap-1.5">
                <div class="rounded-2xl px-4 py-2.5 text-sm leading-relaxed bg-emerald-50 text-gray-800 border border-emerald-100 rounded-bl-md">
                  <p>{{ msg.content }}</p>

                  <!-- Action bar -->
                  <div class="mt-2.5 pt-2 border-t border-emerald-100 flex flex-wrap items-center gap-1">
                    <button
                      type="button"
                      class="ai-action-btn"
                      :class="{ 'ai-action-btn--active': speakingIdx === idx }"
                      title="Nghe lại"
                      @click="replaySpeech(msg, idx)"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                        <path v-if="speakingIdx === idx" d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                      </svg>
                      <span>Phát âm</span>
                    </button>

                    <button
                      type="button"
                      class="ai-action-btn"
                      :class="{ 'ai-action-btn--active': msg.showHint }"
                      :disabled="msg.hintLoading"
                      title="Gợi ý trả lời"
                      @click="toggleHint(msg, idx)"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 18h6"/><path d="M10 22h4"/>
                        <path d="M12 2a7 7 0 0 0-4 12.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26A7 7 0 0 0 12 2z"/>
                      </svg>
                      <span>{{ msg.hintLoading ? '…' : 'Gợi ý' }}</span>
                    </button>

                    <button
                      type="button"
                      class="ai-action-btn"
                      :class="{ 'ai-action-btn--active': msg.showTranslation }"
                      :disabled="msg.translationLoading"
                      title="Dịch sang tiếng Việt"
                      @click="toggleTranslate(msg, idx)"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/>
                        <path d="M2 5h12"/><path d="M7 2h1"/>
                        <path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>
                      </svg>
                      <span>{{ msg.translationLoading ? '…' : 'Dịch' }}</span>
                    </button>
                  </div>

                  <!-- Hint panel -->
                  <div v-if="msg.showHint && msg.hint" class="mt-2 p-2.5 rounded-xl bg-amber-50 border border-amber-100 text-xs space-y-1.5">
                    <p class="font-semibold text-amber-800 flex items-center gap-1">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a7 7 0 0 0-4 12.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26A7 7 0 0 0 12 2z"/></svg>
                      Gợi ý
                    </p>
                    <p class="text-amber-900/80">{{ msg.hint.hint_vi }}</p>
                    <p class="text-gray-700 italic">"{{ msg.hint.example_reply }}"</p>
                    <div v-if="msg.hint.key_phrases?.length" class="flex flex-wrap gap-1 pt-0.5">
                      <button
                        v-for="phrase in msg.hint.key_phrases"
                        :key="phrase"
                        type="button"
                        class="px-1.5 py-0.5 rounded-md bg-white border border-amber-200 text-amber-800 hover:bg-amber-100 transition-colors"
                        @click="usePhrase(phrase)"
                      >
                        {{ phrase }}
                      </button>
                    </div>
                  </div>

                  <!-- Translation panel -->
                  <div v-if="msg.showTranslation && msg.translation" class="mt-2 p-2.5 rounded-xl bg-blue-50 border border-blue-100 text-xs">
                    <p class="font-semibold text-blue-800 flex items-center gap-1 mb-1">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 8 6 6"/><path d="M2 5h12"/><path d="m22 22-5-10-5 10"/></svg>
                      Dịch
                    </p>
                    <p class="text-blue-900/90 leading-relaxed">{{ msg.translation }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="thinking" class="flex justify-start">
              <div class="bg-emerald-50 rounded-2xl px-4 py-2 text-sm text-gray-500 animate-pulse">
                AI đang trả lời…
              </div>
            </div>
          </template>
        </div>

        <!-- Input -->
        <div class="shrink-0 border-t border-gray-100 p-3">
          <p v-if="inputError" class="text-xs text-red-500 mb-2">{{ inputError }}</p>
          <div class="flex items-end gap-2">
            <textarea
              v-model="draft"
              rows="2"
              placeholder="Nhập câu trả lời bằng tiếng Anh…"
              class="flex-1 resize-none rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:border-[#34d399] disabled:bg-gray-50"
              :disabled="!sessionId || thinking || recording"
              @keydown.enter.exact.prevent="sendText"
            />
            <button
              @click="toggleRecording"
              :disabled="!sessionId || thinking"
              class="shrink-0 h-10 w-10 rounded-xl flex items-center justify-center transition-colors"
              :class="recording
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'"
              :title="recording ? 'Dừng ghi âm' : 'Ghi âm'"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="!recording" d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
                <rect v-else x="6" y="6" width="12" height="12" rx="2"/>
                <path v-if="!recording" d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
            </button>
            <button
              @click="sendText"
              :disabled="!sessionId || !draft.trim() || thinking || recording"
              class="shrink-0 h-10 px-4 rounded-xl bg-gray-900 text-white text-sm font-semibold hover:bg-gray-800 disabled:opacity-40 transition-colors"
            >
              Gửi
            </button>
          </div>
          <p v-if="recording" class="text-xs text-red-500 mt-1 text-center">Đang ghi âm… {{ recordSecs }}s</p>
        </div>
      </div>

      <!-- Sidebar: vocabulary + last analysis -->
      <aside class="lg:w-64 shrink-0 mt-4 lg:mt-0 space-y-4">
        <div class="bg-white rounded-2xl border border-gray-200 p-4">
          <h3 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">Từ vựng gợi ý</h3>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="word in vocabulary"
              :key="word"
              class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700"
              :class="usedVocab.has(word.toLowerCase()) ? 'ring-2 ring-[#34d399] bg-emerald-50' : ''"
            >
              {{ word }}
            </span>
          </div>
        </div>

        <div v-if="lastAnalysis" class="bg-white rounded-2xl border border-gray-200 p-4 text-sm">
          <h3 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">Phân tích lượt vừa rồi</h3>
          <div v-if="lastAnalysis.grammar?.score != null" class="mb-2">
            <span class="text-gray-500">Ngữ pháp:</span>
            <span class="font-bold text-gray-900 ml-1">{{ lastAnalysis.grammar.score }}/9</span>
          </div>
          <div v-if="lastAnalysis.vocabulary?.score != null" class="mb-2">
            <span class="text-gray-500">Từ vựng:</span>
            <span class="font-bold text-gray-900 ml-1">{{ lastAnalysis.vocabulary.score }}/9</span>
          </div>
          <ul v-if="lastAnalysis.grammar?.errors?.length" class="mt-2 space-y-1 text-xs text-gray-600">
            <li v-for="(err, i) in lastAnalysis.grammar.errors.slice(0, 2)" :key="i">
              ✏️ {{ err.correction || err.text }}
            </li>
          </ul>
        </div>

        <div class="text-xs text-gray-400 px-1">
          Lượt: {{ turnCount }} · AI: {{ session?.ai_role?.slice(0, 40) }}…
        </div>
      </aside>
    </div>

    <!-- End summary modal -->
    <div v-if="summary" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="summary = null">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl max-h-[80vh] overflow-y-auto">
        <h2 class="text-xl font-black text-gray-900 mb-1">Tổng kết buổi luyện</h2>
        <p class="text-sm text-gray-500 mb-4">{{ summary.turn_count }} lượt hội thoại</p>

        <p class="text-sm text-gray-700 mb-4">{{ summary.feedback?.summary }}</p>

        <div v-if="summary.feedback?.scores" class="grid grid-cols-3 gap-2 mb-4">
          <div v-if="summary.feedback.scores.grammar != null" class="text-center p-2 rounded-xl bg-blue-50">
            <p class="text-xs text-gray-500">Ngữ pháp</p>
            <p class="font-bold text-blue-700">{{ summary.feedback.scores.grammar }}/9</p>
          </div>
          <div v-if="summary.feedback.scores.vocabulary != null" class="text-center p-2 rounded-xl bg-emerald-50">
            <p class="text-xs text-gray-500">Từ vựng</p>
            <p class="font-bold text-emerald-700">{{ summary.feedback.scores.vocabulary }}/9</p>
          </div>
          <div v-if="summary.feedback.scores.pronunciation != null" class="text-center p-2 rounded-xl bg-purple-50">
            <p class="text-xs text-gray-500">Phát âm</p>
            <p class="font-bold text-purple-700">{{ summary.feedback.scores.pronunciation }}/10</p>
          </div>
        </div>

        <div v-if="summary.feedback?.strengths?.length" class="mb-3">
          <p class="text-xs font-bold text-gray-400 uppercase mb-1">Điểm mạnh</p>
          <ul class="text-sm text-gray-700 list-disc pl-4 space-y-0.5">
            <li v-for="(s, i) in summary.feedback.strengths" :key="i">{{ s }}</li>
          </ul>
        </div>
        <div v-if="summary.feedback?.improvements?.length" class="mb-3">
          <p class="text-xs font-bold text-gray-400 uppercase mb-1">Cần cải thiện</p>
          <ul class="text-sm text-gray-700 list-disc pl-4 space-y-0.5">
            <li v-for="(s, i) in summary.feedback.improvements" :key="i">{{ s }}</li>
          </ul>
        </div>

        <button
          @click="goHub"
          class="w-full mt-4 py-2.5 rounded-xl bg-gray-900 text-white font-semibold text-sm hover:bg-gray-800"
        >
          Về danh sách chủ đề
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  startConversation,
  sendTurn,
  sendVoiceTurn,
  endConversation,
  fetchReplyHint,
  translateAiMessage,
} from '@/services/conversationService.js'
import { speakEnglish, stopSpeaking } from '@/utils/vocabSpeech.js'

const route = useRoute()
const router = useRouter()
const topicId = Number(route.params.topicId)

const initLoading = ref(true)
const session = ref(null)
const sessionId = ref(null)
const messages = ref([])
const vocabulary = ref([])
const draft = ref('')
const thinking = ref(false)
const inputError = ref('')
const turnCount = ref(0)
const lastAnalysis = ref(null)
const usedVocab = ref(new Set())
const summary = ref(null)
const ending = ref(false)
const chatRef = ref(null)
const speakingIdx = ref(null)

const recording = ref(false)
const recordSecs = ref(0)
let mediaRecorder = null
let mediaStream = null
let chunks = []
let recordTimer = null

function scrollBottom() {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
}

function makeAssistantMessage(content) {
  return {
    role: 'assistant',
    content,
    hint: null,
    hintLoading: false,
    showHint: false,
    translation: null,
    translationLoading: false,
    showTranslation: false,
  }
}

async function autoSpeakAssistant(msg, idx) {
  speakingIdx.value = idx
  await speakEnglish(msg.content, 0.88, idx)
  if (speakingIdx.value === idx) speakingIdx.value = null
}

function replaySpeech(msg, idx) {
  if (speakingIdx.value === idx) {
    stopSpeaking()
    speakingIdx.value = null
    return
  }
  autoSpeakAssistant(msg, idx)
}

async function toggleHint(msg, idx) {
  msg.showHint = !msg.showHint
  if (!msg.showHint || msg.hint || msg.hintLoading) return
  msg.hintLoading = true
  try {
    msg.hint = await fetchReplyHint(sessionId.value, msg.content)
  } catch (e) {
    inputError.value = e?.response?.data?.detail || 'Không tải được gợi ý.'
    msg.showHint = false
  } finally {
    msg.hintLoading = false
  }
}

async function toggleTranslate(msg, idx) {
  msg.showTranslation = !msg.showTranslation
  if (!msg.showTranslation || msg.translation || msg.translationLoading) return
  msg.translationLoading = true
  try {
    const data = await translateAiMessage(msg.content)
    msg.translation = data.translation
  } catch (e) {
    inputError.value = e?.response?.data?.detail || 'Không dịch được.'
    msg.showTranslation = false
  } finally {
    msg.translationLoading = false
  }
}

function usePhrase(phrase) {
  draft.value = draft.value.trim() ? `${draft.value.trim()} ${phrase}` : phrase
}

function goBack() {
  if (sessionId.value && !summary.value) {
    if (confirm('Kết thúc buổi luyện và quay lại?')) finishSession()
    else router.push('/conversation')
  } else {
    router.push('/conversation')
  }
}

function goHub() {
  summary.value = null
  router.push('/conversation')
}

async function initSession() {
  initLoading.value = true
  try {
    const data = await startConversation(topicId)
    session.value = data
    sessionId.value = data.session_id
    vocabulary.value = data.vocabulary || []
    const opening = makeAssistantMessage(data.opening_line)
    messages.value = [opening]
    scrollBottom()
    autoSpeakAssistant(opening, 0)
  } catch (e) {
    inputError.value = e?.response?.data?.detail || 'Không khởi tạo được phiên hội thoại.'
  } finally {
    initLoading.value = false
  }
}

function applyTurnResult(data, userContent, isVoice = false) {
  turnCount.value = data.turn_count
  lastAnalysis.value = { grammar: data.grammar, vocabulary: data.vocabulary }

  const used = data.analysis?.used_vocab || []
  used.forEach(w => usedVocab.value.add(String(w).toLowerCase()))

  messages.value.push({
    role: 'user',
    content: isVoice ? (data.transcript || userContent) : userContent,
    feedback: data.analysis,
    pronunciation: data.pronunciation,
  })
  const aiMsg = makeAssistantMessage(data.ai_reply)
  messages.value.push(aiMsg)
  scrollBottom()
  autoSpeakAssistant(aiMsg, messages.value.length - 1)
}

async function sendText() {
  const text = draft.value.trim()
  if (!text || !sessionId.value || thinking.value) return
  inputError.value = ''
  draft.value = ''
  thinking.value = true
  try {
    const data = await sendTurn(sessionId.value, text)
    applyTurnResult(data, text)
  } catch (e) {
    inputError.value = e?.response?.data?.detail || 'Gửi thất bại, thử lại.'
    draft.value = text
  } finally {
    thinking.value = false
  }
}

function pickMimeType() {
  const c = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
  return c.find(t => MediaRecorder.isTypeSupported(t)) || ''
}

function cleanupRecording() {
  if (recordTimer) { clearInterval(recordTimer); recordTimer = null }
  if (mediaRecorder?.state !== 'inactive') {
    try { mediaRecorder.stop() } catch { /* ignore */ }
  }
  mediaStream?.getTracks().forEach(t => t.stop())
  mediaRecorder = null
  mediaStream = null
  chunks = []
  recording.value = false
}

async function toggleRecording() {
  if (recording.value) {
    mediaRecorder?.stop()
    return
  }
  inputError.value = ''
  chunks = []
  recordSecs.value = 0
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mime = pickMimeType()
    mediaRecorder = mime
      ? new MediaRecorder(mediaStream, { mimeType: mime })
      : new MediaRecorder(mediaStream)
    mediaRecorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data) }
    mediaRecorder.onstop = async () => {
      const mimeType = mediaRecorder?.mimeType || 'audio/webm'
      const blob = new Blob(chunks, { type: mimeType })
      cleanupRecording()
      if (!blob.size) return
      thinking.value = true
      try {
        const ext = blob.type.includes('mp4') ? 'recording.mp4' : 'recording.webm'
        const data = await sendVoiceTurn(sessionId.value, blob, ext)
        applyTurnResult(data, data.transcript, true)
      } catch (e) {
        inputError.value = e?.response?.data?.detail || 'Ghi âm thất bại, thử lại.'
      } finally {
        thinking.value = false
      }
    }
    mediaRecorder.start()
    recording.value = true
    recordTimer = setInterval(() => { recordSecs.value++ }, 1000)
    setTimeout(() => { if (recording.value) mediaRecorder?.stop() }, 30000)
  } catch {
    inputError.value = 'Không truy cập được microphone.'
    cleanupRecording()
  }
}

async function finishSession() {
  if (!sessionId.value || ending.value) return
  ending.value = true
  try {
    summary.value = await endConversation(sessionId.value)
  } catch (e) {
    inputError.value = e?.response?.data?.detail || 'Không kết thúc được phiên.'
  } finally {
    ending.value = false
  }
}

onMounted(initSession)
onUnmounted(() => {
  cleanupRecording()
  stopSpeaking()
})
</script>

<style scoped>
.ai-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  color: #059669;
  background: transparent;
  border: 1px solid transparent;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.ai-action-btn:hover:not(:disabled) {
  background: #ecfdf5;
  border-color: #a7f3d0;
}
.ai-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.ai-action-btn--active {
  background: #d1fae5;
  border-color: #34d399;
  color: #047857;
}
</style>

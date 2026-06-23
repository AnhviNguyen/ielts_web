<template>
  <div class="shadowing-studio flex h-screen min-h-0 flex-col">
    <header class="flex shrink-0 flex-wrap items-center gap-3 border-b border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="t in tabs"
          :key="t.id"
          type="button"
          class="sh-tab"
          :class="{ 'is-active': activeTab === t.id }"
          @click="activeTab = t.id"
        >
          {{ t.label }}
        </button>
      </div>
      <div class="ml-auto flex items-center gap-2">
        <button type="button" class="sh-btn gap-2 text-[12px]" @click="showVideo = !showVideo">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="showVideo" d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
            <line v-if="showVideo" x1="1" y1="1" x2="23" y2="23"/>
            <template v-else>
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </template>
          </svg>
          {{ showVideo ? 'Ẩn video' : 'Hiện video' }}
        </button>
        <button type="button" class="sh-btn text-[12px]" @click="$emit('back')">Quay lại</button>
      </div>
    </header>

    <div class="sh-studio-grid min-h-0 w-full max-w-full flex-1 overflow-hidden">
      <!-- Cột trái — video + điều khiển; chỉ cột này cuộn dọc -->
      <div class="sh-left-col min-h-0 border-r border-[var(--border)] bg-[var(--bg-surface)]">
        <div class="sh-left-col-scroll">
          <header class="sh-video-meta">
            <button
              type="button"
              class="flex items-center gap-1 text-left text-[12px] font-semibold text-[var(--ink2)] hover:text-[var(--ink)]"
              @click="$emit('back')"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
              Quay lại · {{ videoData.level }}
            </button>
            <h1 class="sh-video-title">{{ videoData.title }}</h1>
          </header>

          <div v-show="showVideo" class="sh-video-shell">
            <div ref="playerHost" class="sh-video-player" />
          </div>

          <div class="sh-left-controls">
        <template v-if="activeTab === 'shadowing'">
          <p class="sh-panel-title">Điều khiển</p>
          <ShadowingPlaybackControls
            :playing="playing"
            :rate="playbackRate"
            :compact="false"
            @prev="prevSegment"
            @replay="replaySegment"
            @next="nextSegment"
            @toggle-play="onTogglePlay"
            @update:rate="playbackRate = $event"
          />
          <label class="flex cursor-pointer items-center gap-2 text-[12px] font-medium text-[var(--ink2)]">
            <input v-model="showTranslation" type="checkbox" class="rounded border-[var(--border)] text-[var(--spotify-green)]" />
            Bản dịch
          </label>
        </template>

        <template v-else-if="activeTab === 'dictation'">
          <p class="sh-panel-title">Điều khiển</p>
          <div class="grid grid-cols-2 gap-2">
            <button type="button" class="sh-btn sh-btn-primary sh-btn-block" @click="onTogglePlay">
              {{ playing ? 'Tạm dừng' : 'Phát' }}
            </button>
            <button type="button" class="sh-btn sh-btn-block" @click="onDictationReplay">Phát lại</button>
            <button type="button" class="sh-btn sh-btn-primary sh-btn-block" @click="dictationRef?.onCheck?.()">Kiểm tra</button>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="sh-card p-3">
              <div class="text-[10px] font-bold uppercase text-gray-500">Lỗi sai</div>
              <div class="text-2xl font-bold text-rose-600">{{ dictationErrors }}</div>
            </div>
            <div class="sh-card p-3">
              <div class="text-[10px] font-bold uppercase text-gray-500">Lượt phát lại</div>
              <div class="text-2xl font-bold text-black">{{ dictationReplays }}</div>
            </div>
          </div>
          <div class="sh-card border-amber-200 bg-amber-50 p-3 text-[11px] leading-relaxed text-amber-900">
            <span class="font-bold">Lý do:</span> Nghe và gõ lại câu. Nhấn biểu tượng mắt từng từ ở giữa hoặc bản chép để gợi ý.
          </div>
          <div class="sh-card p-3">
            <div class="text-[10px] font-bold uppercase text-gray-500">Điểm lần trước</div>
            <div class="text-xl font-bold text-[var(--spotify-green)]">{{ dictationLastScore ?? '—' }}</div>
          </div>
          <ShadowingPlaybackControls
            :playing="playing"
            :rate="playbackRate"
            :compact="true"
            @prev="prevSegment"
            @replay="onDictationReplay"
            @next="nextSegment"
            @toggle-play="onTogglePlay"
            @update:rate="playbackRate = $event"
          />
        </template>

        <template v-else>
          <p class="sh-panel-title">Ghi âm phát âm</p>
          <button type="button" class="sh-btn sh-btn-primary sh-btn-block gap-2 py-3" :disabled="pronunciationRef?.checking" @click="pronunciationRef?.toggleRecord?.()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            </svg>
            {{ pronunciationRef?.checking ? 'Đang phân tích...' : pronunciationRef?.listening ? 'Đang ghi...' : 'Ghi âm' }}
          </button>
          <button
            type="button"
            class="sh-btn sh-btn-block"
            :disabled="!pronunciationRef?.lastBlobUrl"
            @click="pronunciationRef?.playRecording?.()"
          >
            Phát lại ghi âm
          </button>
          <div class="sh-card p-3">
            <div class="mb-1 flex items-center gap-1 text-[10px] font-bold uppercase text-gray-500">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
              Điểm phát âm
            </div>
            <div class="text-3xl font-bold text-black">{{ pronunciationScoreDisplay }}</div>
          </div>
          <div class="sh-card border-amber-200 bg-amber-50 p-3 text-[11px] italic text-amber-900">
            <span class="font-bold not-italic">Mẹo:</span> {{ pronunciationTipDisplay }}
          </div>
          <ShadowingPlaybackControls
            :playing="playing"
            :rate="playbackRate"
            :compact="true"
            :show-speed="false"
            @prev="prevSegment"
            @replay="replaySegment"
            @next="nextSegment"
            @toggle-play="onTogglePlay"
            @update:rate="playbackRate = $event"
          />
        </template>
          </div>
        </div>
      </div>

      <!-- Cột giữa — card (2) -->
      <div class="sh-middle-panel flex min-h-0 min-w-0 flex-col border-r border-[var(--border-button)]">
        <ShadowingFocusCard
          v-if="activeTab === 'shadowing'"
          :segment="currentSegment"
          :show-translation="showTranslation"
          :source-quiz-id="videoData.video_id"
        />
        <DictationTab
          v-else-if="activeTab === 'dictation'"
          ref="dictationRef"
          :segment="currentSegment"
          :segment-index="currentIndex"
          :revealed-word-keys="dictationRevealedKeys"
          @scored="onDictationScored"
          @next="nextSegment"
          @replay="onDictationReplay"
          @reveal-word="onRevealWord"
          @reveal-all="onRevealAllWords"
        />
        <PronunciationTab
          v-else
          ref="pronunciationRef"
          :segment="currentSegment"
          :show-translation="showTranslation"
          :segment-index="currentIndex"
          :source-quiz-id="videoData.video_id"
          @scored="onPronunciationScored"
        />
      </div>

      <!-- Cột phải — transcript (3) -->
      <div class="flex min-h-0 min-w-0 flex-col overflow-hidden max-lg:min-h-[40vh]">
        <ShadowingTranscriptPanel
          v-model:show-translation="showTranslation"
          :segments="segments"
          :active-index="currentIndex"
          :flagged-ids="flaggedIds"
          :dictation-mode="activeTab === 'dictation'"
          :revealed-word-keys="dictationRevealedKeys"
          :vocab-enabled="activeTab !== 'dictation'"
          :source-quiz-id="videoData.video_id"
          @seek="onTranscriptSeek"
          @toggle-flag="toggleFlag"
          @reveal-word="onRevealWord"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, toRef, nextTick } from 'vue'
import { useShadowingSession } from '@/composables/useShadowingSession.js'
import { touchShadowingHistory } from '@/services/shadowingService.js'
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'
import { loadProgress, saveProgress, saveVideoMeta } from '@/utils/shadowingProgress.js'
import ShadowingFocusCard from '@/components/shadowing/ShadowingFocusCard.vue'
import DictationTab from '@/components/shadowing/tabs/DictationTab.vue'
import PronunciationTab from '@/components/shadowing/tabs/PronunciationTab.vue'
import ShadowingTranscriptPanel from '@/components/shadowing/ShadowingTranscriptPanel.vue'
import ShadowingPlaybackControls from '@/components/shadowing/ShadowingPlaybackControls.vue'
const props = defineProps({
  videoData: { type: Object, required: true },
})

defineEmits(['back'])

const videoDataRef = toRef(props, 'videoData')

const {
  playing,
  mountPlayer: mountYtPlayer,
  destroyPlayer,
  currentIndex,
  playbackRate,
  showVideo,
  showTranslation,
  flaggedIds,
  segments,
  currentSegment,
  loadSaved,
  playSegment,
  nextSegment,
  prevSegment,
  replaySegment,
  toggleFlag,
  onTimeUpdate,
  pause,
  play,
} = useShadowingSession(videoDataRef)

const activeTab = ref('shadowing')
const playerHost = ref(null)
const dictationRef = ref(null)
const pronunciationRef = ref(null)
const dictationRevealedKeys = ref(new Set())

const tabs = [
  { id: 'shadowing', label: 'Bắt chước phát âm' },
  { id: 'dictation', label: 'Nghe - Viết chính tả' },
  { id: 'pronunciation', label: 'Chỉnh phát âm' },
]

const dictationErrors = computed(() => dictationRef.value?.lastResult?.wrong?.length ?? 0)
const dictationReplays = computed(() => dictationRef.value?.replayCount ?? 0)
const dictationLastScore = computed(() => dictationRef.value?.lastScore ?? null)

const pronunciationScoreDisplay = computed(() => pronunciationRef.value?.score ?? '—')

const pronunciationTipDisplay = computed(() => {
  const t = pronunciationRef.value?.tip
  return typeof t === 'string' ? t : 'Nói rõ từng âm tiết, chú ý ngữ điệu lên xuống.'
})

function onRevealWord(segId, wi) {
  const key = `${segId}-${wi}`
  const next = new Set(dictationRevealedKeys.value)
  next.add(key)
  dictationRevealedKeys.value = next
}

function onRevealAllWords(segId, wordCount) {
  const next = new Set(dictationRevealedKeys.value)
  for (let wi = 0; wi < wordCount; wi++) next.add(`${segId}-${wi}`)
  dictationRevealedKeys.value = next
}

function onTranscriptSeek(idx) {
  playSegment(idx, { autoPlay: true })
}

function onDictationReplay() {
  dictationRef.value?.onReplay?.()
  replaySegment()
}

function onTogglePlay() {
  if (playing.value) pause()
  else playSegment(currentIndex.value)
}

function onDictationScored({ index, score }) {
  const vid = props.videoData.video_id
  const p = loadProgress(vid)
  const scores = [...(p.dictationScores || [])]
  scores[index] = score
  saveProgress(vid, { dictationScores: scores })
}

function onPronunciationScored({ index, score }) {
  const vid = props.videoData.video_id
  const p = loadProgress(vid)
  const scores = [...(p.pronunciationScores || [])]
  scores[index] = score
  saveProgress(vid, { pronunciationScores: scores })
}

function onKeydown(e) {
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return
  if (e.code === 'Space') {
    e.preventDefault()
    onTogglePlay()
  } else if (e.code === 'KeyR') {
    replaySegment()
  } else if (e.code === 'ArrowRight') {
    nextSegment()
  } else if (e.code === 'ArrowLeft') {
    prevSegment()
  }
}

watch(activeTab, (tab) => {
  if (tab !== 'dictation') dictationRevealedKeys.value = new Set()
  playSegment(currentIndex.value, { autoPlay: playing.value })
})

async function mountPlayer() {
  if (!playerHost.value) return
  await mountYtPlayer(playerHost.value, props.videoData.video_id, {
    onTimeUpdate,
  })
  playSegment(currentIndex.value, { autoPlay: true })
}

const badgeCelebration = useBadgeCelebrationStore()

onMounted(async () => {
  const vid = props.videoData.video_id
  loadSaved(vid)
  saveVideoMeta(vid, {
    title: props.videoData.title,
    level: props.videoData.level,
    sourceUrl: props.videoData.source_url,
  })
  touchShadowingHistory(vid)
    .then((res) => badgeCelebration.enqueue(res?.new_badges))
    .catch(() => {})
  window.addEventListener('keydown', onKeydown)
  await mountPlayer()
})

watch(playerHost, async (el) => {
  if (el && showVideo.value) await mountPlayer()
})
watch(showVideo, async (show) => {
  if (!show) {
    destroyPlayer()
    return
  }
  await nextTick()
  await mountPlayer()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  destroyPlayer()
})
</script>

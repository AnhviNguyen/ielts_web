<template>
  <ShadowingStudio
    v-if="videoData"
    :video-data="videoData"
    @back="onBack"
  />

  <div v-else class="hub-page">
    <section class="section-compact">
      <div class="app-container max-w-2xl">
        <div class="spotify-panel">
          <div class="spotify-panel__header">
            <h1 class="font-display" data-tour="page-header">Shadowing</h1>
            <p class="page-subtitle">
              Bắt chước phát âm, nghe chép và luyện phát âm từ video YouTube — transcript tự động đồng bộ.
            </p>
          </div>
          <div class="spotify-panel__body">
    <div class="ct-card p-6" data-tour="shadowing-url">
      <label class="mb-2 block text-xs font-bold uppercase tracking-wide text-[var(--ink3)]">Link YouTube</label>
      <input
        v-model="urlInput"
        type="url"
        class="ct-input mb-3 w-full"
        placeholder="https://www.youtube.com/watch?v=..."
        @keydown.enter="process"
      />

      <div class="mb-4 flex flex-wrap items-center gap-3">
        <label class="text-[12px] text-[var(--ink2)]">Trình độ</label>
        <select v-model="level" class="ct-select max-w-[200px]">
          <option value="Beginner">Beginner</option>
          <option value="Intermediate">Intermediate</option>
          <option value="Advanced">Advanced</option>
          <option value="IELTS 6.0">IELTS 6.0</option>
          <option value="IELTS 7.0">IELTS 7.0</option>
        </select>
        <label class="flex items-center gap-1.5 text-[12px] text-[var(--ink2)]">
          <input v-model="translate" type="checkbox" class="rounded" />
          Dịch sang Tiếng Việt
        </label>
      </div>

      <p v-if="error" class="mb-3 text-xs text-rose-600">{{ error }}</p>

      <button
        type="button"
        class="sh-btn sh-btn-primary w-full sm:w-auto px-6 py-2.5"
        :disabled="processing || !urlInput.trim()"
        @click="process"
      >
        {{ processing ? 'Đang xử lý transcript…' : 'Bắt đầu luyện tập' }}
      </button>
      <p v-if="processing" class="mt-3 text-[11px] text-[var(--ink3)]">
        Đang lấy phụ đề EN từ YouTube (vài giây)…
      </p>
    </div>

    <section v-if="historyLoading || historyItems.length" class="mt-6 border-t border-[var(--border-button)] pt-6">
      <div class="mb-3 flex items-center justify-between gap-2">
        <h2 class="text-sm font-bold text-[var(--ink)]">Lịch sử đã xem</h2>
        <span v-if="historyLoading" class="text-[11px] text-[var(--ink3)]">Đang tải…</span>
      </div>

      <ul v-if="historyItems.length" class="space-y-2">
        <li
          v-for="item in historyItems"
          :key="item.video_id"
          class="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] overflow-hidden"
        >
          <!-- Chế độ sửa -->
          <div v-if="editingId === item.video_id" class="p-3 space-y-2">
            <label class="block text-[10px] font-bold uppercase text-gray-500">Tên hiển thị</label>
            <input v-model="editForm.title" type="text" class="ct-input w-full text-[13px]" />
            <label class="block text-[10px] font-bold uppercase text-gray-500">Trình độ</label>
            <select v-model="editForm.level" class="ct-select w-full text-[13px]">
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
              <option value="IELTS 6.0">IELTS 6.0</option>
              <option value="IELTS 7.0">IELTS 7.0</option>
            </select>
            <div class="flex gap-2 pt-1">
              <button type="button" class="sh-btn sh-btn-primary flex-1 text-[12px]" :disabled="historySaving" @click="saveEdit(item)">
                Lưu
              </button>
              <button type="button" class="sh-btn flex-1 text-[12px]" @click="cancelEdit">Hủy</button>
            </div>
          </div>

          <!-- Dòng danh sách -->
          <div v-else class="flex items-stretch gap-0">
            <button
              type="button"
              class="flex min-w-0 flex-1 items-start gap-3 p-3 text-left transition-colors hover:bg-emerald-50/40"
              @click="openHistoryItem(item)"
            >
              <div class="relative h-[63px] w-28 shrink-0 overflow-hidden rounded-lg bg-gray-100">
                <img
                  :src="thumbUrl(item)"
                  :alt="item.title"
                  class="h-full w-full object-cover"
                  loading="lazy"
                  @error="onThumbError($event, item.video_id)"
                />
                <div
                  v-if="thumbFailed[item.video_id]"
                  class="absolute inset-0 flex items-center justify-center bg-gray-200 text-gray-500"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                </div>
              </div>
              <div class="min-w-0 flex-1 py-0.5">
                <p class="line-clamp-2 text-[13px] font-semibold leading-snug text-[var(--ink)]">
                  {{ item.title }}
                </p>
                <p class="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-[var(--ink3)]">
                  <span class="rounded bg-gray-100 px-1.5 py-0.5 font-medium text-gray-700">{{ item.level }}</span>
                  <span v-if="item.segment_count">{{ item.segment_count }} câu</span>
                  <span>{{ formatHistoryDate(item.last_viewed_at) }}</span>
                </p>
              </div>
            </button>
            <div class="flex shrink-0 flex-col justify-center gap-1 border-l border-gray-100 px-2">
              <button
                type="button"
                class="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-emerald-700"
                title="Sửa"
                @click="startEdit(item)"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button
                type="button"
                class="rounded-lg p-2 text-gray-500 hover:bg-rose-50 hover:text-rose-600"
                title="Xóa khỏi lịch sử"
                @click="deleteHistoryItem(item)"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
        </li>
      </ul>
      <p v-else-if="!historyLoading" class="text-[12px] text-[var(--ink3)]">Chưa có bài nào trong lịch sử.</p>
    </section>

          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ShadowingStudio from '@/components/shadowing/ShadowingStudio.vue'
import {
  processVideo,
  getVideo,
  getShadowingHistory,
  updateShadowingHistory,
  deleteShadowingHistory,
} from '@/services/shadowingService.js'
import { extractYoutubeVideoId, youtubeThumbnail } from '@/utils/segmentUtils.js'
import { fetchYoutubeCaptionsClient } from '@/utils/youtubeClientTranscript.js'
import {
  listLocalHistory,
  saveVideoMeta,
  updateLocalHistoryMeta,
  removeLocalHistory,
} from '@/utils/shadowingProgress.js'

const route = useRoute()
const router = useRouter()

const videoData = ref(null)
const urlInput = ref('')
const level = ref('Intermediate')
const translate = ref(true)
const processing = ref(false)
const error = ref('')
const historyItems = ref([])
const historyLoading = ref(false)
const editingId = ref(null)
const editForm = ref({ title: '', level: 'Intermediate' })
const historySaving = ref(false)
const thumbFailed = reactive({})

function thumbUrl(item) {
  return item.thumbnail_url || youtubeThumbnail(item.video_id)
}

function onThumbError(_e, videoId) {
  thumbFailed[videoId] = true
}

function mergeHistory(apiItems, localItems) {
  const byId = new Map()
  for (const item of apiItems || []) {
    byId.set(item.video_id, { ...item, _local: false })
  }
  for (const item of localItems || []) {
    if (!byId.has(item.video_id)) {
      byId.set(item.video_id, {
        ...item,
        thumbnail_url: youtubeThumbnail(item.video_id),
        _local: true,
      })
    }
  }
  return [...byId.values()].sort((a, b) => {
    const ta = a.last_viewed_at ? new Date(a.last_viewed_at).getTime() : 0
    const tb = b.last_viewed_at ? new Date(b.last_viewed_at).getTime() : 0
    return tb - ta
  })
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const api = await getShadowingHistory(30)
    historyItems.value = mergeHistory(api, listLocalHistory())
  } catch {
    historyItems.value = listLocalHistory().map((item) => ({
      ...item,
      thumbnail_url: youtubeThumbnail(item.video_id),
    }))
  } finally {
    historyLoading.value = false
  }
}

function formatHistoryDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ''
  }
}

function startEdit(item) {
  editingId.value = item.video_id
  editForm.value = { title: item.title, level: item.level }
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(item) {
  historySaving.value = true
  error.value = ''
  try {
    if (item._local) {
      updateLocalHistoryMeta(item.video_id, {
        title: editForm.value.title,
        level: editForm.value.level,
      })
      item.title = editForm.value.title
      item.level = editForm.value.level
    } else {
      const updated = await updateShadowingHistory(item.video_id, {
        title: editForm.value.title,
        level: editForm.value.level,
      })
      const idx = historyItems.value.findIndex((h) => h.video_id === item.video_id)
      if (idx >= 0) historyItems.value[idx] = { ...historyItems.value[idx], ...updated }
    }
    editingId.value = null
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Không lưu được thay đổi.'
  } finally {
    historySaving.value = false
  }
}

async function deleteHistoryItem(item) {
  if (!confirm(`Xóa "${item.title}" khỏi lịch sử?`)) return
  error.value = ''
  try {
    if (item._local) {
      removeLocalHistory(item.video_id)
    } else {
      await deleteShadowingHistory(item.video_id)
    }
    historyItems.value = historyItems.value.filter((h) => h.video_id !== item.video_id)
    if (editingId.value === item.video_id) editingId.value = null
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Không xóa được mục lịch sử.'
  }
}

async function openHistoryItem(item) {
  error.value = ''
  processing.value = true
  try {
    videoData.value = await getVideo(item.video_id)
    saveVideoMeta(item.video_id, {
      title: videoData.value.title,
      level: videoData.value.level,
      sourceUrl: videoData.value.source_url,
    })
    router.push({ name: 'ShadowingPractice', params: { videoId: item.video_id } })
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Không mở được video này.'
  } finally {
    processing.value = false
  }
}

async function loadById(videoId) {
  error.value = ''
  processing.value = true
  try {
    videoData.value = await getVideo(videoId)
    saveVideoMeta(videoId, {
      title: videoData.value.title,
      level: videoData.value.level,
      sourceUrl: videoData.value.source_url,
    })
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Chưa có transcript. Dán link và bấm Bắt đầu.'
    videoData.value = null
  } finally {
    processing.value = false
  }
}

async function process() {
  const url = urlInput.value.trim()
  if (!url) return
  const id = extractYoutubeVideoId(url)
  if (!id) {
    error.value = 'Link YouTube không hợp lệ.'
    return
  }
  error.value = ''
  processing.value = true
  try {
    // Video đã xử lý trước — mở luôn (TED trong lịch sử không cần lấy phụ đề lại)
    try {
      const cached = await getVideo(id)
      if (cached?.segments?.length) {
        videoData.value = cached
        saveVideoMeta(id, {
          title: cached.title,
          level: cached.level,
          sourceUrl: cached.source_url,
        })
        router.replace({ name: 'ShadowingPractice', params: { videoId: id } })
        return
      }
    } catch {
      /* chưa có trong DB */
    }

    const client = await fetchYoutubeCaptionsClient(id)
    videoData.value = await processVideo(url, {
      level: level.value,
      translate: translate.value,
      clientSegments: client.segments,
      clientLanguage: client.language,
    })
    saveVideoMeta(videoData.value.video_id, {
      title: videoData.value.title,
      level: videoData.value.level,
      sourceUrl: videoData.value.source_url,
    })
    router.replace({ name: 'ShadowingPractice', params: { videoId: videoData.value.video_id } })
  } catch (e) {
    error.value = e?.response?.data?.detail || e.message || 'Xử lý video thất bại.'
  } finally {
    processing.value = false
  }
}

function onBack() {
  videoData.value = null
  router.push({ name: 'Shadowing' })
  loadHistory()
}

watch(
  () => route.params.videoId,
  (id) => {
    if (id) loadById(id)
    else {
      videoData.value = null
      loadHistory()
    }
  },
  { immediate: true },
)

onMounted(() => {
  if (route.query.url) urlInput.value = String(route.query.url)
  if (!route.params.videoId) loadHistory()
})
</script>

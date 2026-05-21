/**
 * Shared shadowing session — segment sync, continuous playback.
 */
import { ref, computed, watch } from 'vue'
import { useYoutubePlayer } from '@/composables/useYoutubePlayer.js'
import { loadProgress, saveProgress } from '@/utils/shadowingProgress.js'

export function useShadowingSession(videoDataRef) {
  const yt = useYoutubePlayer()
  const currentIndex = ref(0)
  const playbackRate = ref(1)
  const showVideo = ref(true)
  const showTranslation = ref(true)
  const flaggedIds = ref([])

  const segments = computed(() => videoDataRef.value?.segments ?? [])
  const currentSegment = computed(() => segments.value[currentIndex.value] ?? null)

  function loadSaved(videoId) {
    const p = loadProgress(videoId)
    currentIndex.value = Math.min(p.currentSegment, Math.max(0, segments.value.length - 1))
    flaggedIds.value = [...(p.flaggedSegments || [])]
  }

  function persist(videoId) {
    saveProgress(videoId, {
      currentSegment: currentIndex.value,
      flaggedSegments: [...flaggedIds.value],
    })
  }

  function findIndexAtTime(time) {
    const segs = segments.value
    if (!segs.length) return 0
    let idx = 0
    for (let i = 0; i < segs.length; i++) {
      if (time >= (segs[i].start ?? 0) - 0.02) idx = i
    }
    return idx
  }

  function syncIndexFromTime(time) {
    const idx = findIndexAtTime(time)
    if (idx !== currentIndex.value) {
      currentIndex.value = idx
    }
    return idx
  }

  /**
   * @param {number} index
   * @param {{ autoPlay?: boolean | null }} opts — null = giữ trạng thái play/pause hiện tại
   */
  function playSegment(index = currentIndex.value, { autoPlay = true } = {}) {
    const seg = segments.value[index]
    if (!seg) return
    currentIndex.value = index
    yt.seekTo(seg.start)
    if (autoPlay === true) yt.play()
    else if (autoPlay === false) yt.pause()
  }

  function nextSegment() {
    if (currentIndex.value < segments.value.length - 1) {
      playSegment(currentIndex.value + 1, { autoPlay: playing.value })
    }
  }

  function prevSegment() {
    if (currentIndex.value > 0) {
      playSegment(currentIndex.value - 1, { autoPlay: playing.value })
    }
  }

  function replaySegment() {
    playSegment(currentIndex.value, { autoPlay: playing.value })
  }

  function toggleFlag(id) {
    const ids = new Set(flaggedIds.value)
    if (ids.has(id)) ids.delete(id)
    else ids.add(id)
    flaggedIds.value = [...ids]
    const vid = videoDataRef.value?.video_id
    if (vid) persist(vid)
  }

  /** Chỉ cập nhật highlight theo thời gian — không pause, không seek. */
  function onTimeUpdate(time) {
    syncIndexFromTime(time)
  }

  watch(playbackRate, (r) => yt.setRate(r))

  watch(currentIndex, (i) => {
    const vid = videoDataRef.value?.video_id
    if (vid) saveProgress(vid, { currentSegment: i })
  })

  const playing = yt.playing

  return {
    playing,
    playerReady: yt.ready,
    mountPlayer: yt.mount,
    destroyPlayer: yt.destroy,
    currentIndex,
    playbackRate,
    showVideo,
    showTranslation,
    flaggedIds,
    segments,
    currentSegment,
    loadSaved,
    persist,
    playSegment,
    nextSegment,
    prevSegment,
    replaySegment,
    toggleFlag,
    onTimeUpdate,
    pause: yt.pause,
    play: yt.play,
  }
}

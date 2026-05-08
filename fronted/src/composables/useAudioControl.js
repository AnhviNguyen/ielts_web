import { onUnmounted, ref, watch } from 'vue'

/**
 * Wraps a native <audio> element with reactive state + helpers.
 *
 * Usage:
 *   const audio = useAudioControl()
 *   onMounted(() => audio.attach(nativeAudioEl.value))
 *   defineExpose({ seekAndPlay: audio.seekAndPlay })
 */
export function useAudioControl() {
  const audioEl      = ref(null)
  const playing      = ref(false)
  const currentTime  = ref(0)
  const duration     = ref(0)
  const playbackRate = ref(1)

  // ── debounced timeupdate (50 ms) ─────────────────────────────────
  let _debounce = null
  function _onTime() {
    clearTimeout(_debounce)
    _debounce = setTimeout(() => {
      if (audioEl.value) currentTime.value = audioEl.value.currentTime || 0
    }, 50)
  }
  function _onPlay()  { playing.value = true }
  function _onPause() { playing.value = false }
  function _onMeta()  { if (audioEl.value) duration.value = audioEl.value.duration || 0 }

  const _handlers = {
    play: _onPlay, pause: _onPause, timeupdate: _onTime,
    loadedmetadata: _onMeta, durationchange: _onMeta,
  }

  // ── lifecycle ─────────────────────────────────────────────────────
  function attach(el) {
    if (!el) return
    audioEl.value = el
    Object.entries(_handlers).forEach(([evt, fn]) => el.addEventListener(evt, fn))
    el.playbackRate = playbackRate.value
  }

  function detach() {
    clearTimeout(_debounce)
    const el = audioEl.value
    if (!el) return
    Object.entries(_handlers).forEach(([evt, fn]) => el.removeEventListener(evt, fn))
  }

  onUnmounted(detach)

  // ── controls ──────────────────────────────────────────────────────
  function toggle() {
    const a = audioEl.value; if (!a) return
    a.paused ? a.play().catch(() => {}) : a.pause()
  }

  function seekDelta(delta) {
    const a = audioEl.value; if (!a) return
    a.currentTime = Math.max(0, Math.min(a.duration || 0, (a.currentTime || 0) + delta))
  }

  function seekTo(sec) {
    const a = audioEl.value; if (!a) return
    a.currentTime = Math.max(0, Math.min(a.duration || 0, Number(sec) || 0))
  }

  /** Seek to `sec` then start playback immediately. */
  function seekAndPlay(sec) {
    seekTo(sec)
    audioEl.value?.play().catch(() => {})
  }

  function fmt(sec) {
    const s = Math.max(0, Number(sec) || 0)
    return `${Math.floor(s / 60).toString().padStart(2, '0')}:${Math.floor(s % 60).toString().padStart(2, '0')}`
  }

  watch(playbackRate, (v) => { if (audioEl.value) audioEl.value.playbackRate = v })

  return {
    audioEl, playing, currentTime, duration, playbackRate,
    attach, detach, toggle, seekTo, seekDelta, seekAndPlay, fmt,
  }
}

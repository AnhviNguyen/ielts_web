/**
 * src/composables/useRecorder.js
 * ──────────────────────────────
 * SRP: Chỉ xử lý trạng thái recording.
 * Không bao gồm UI logic.
 */
import { ref, onUnmounted } from 'vue'

export function useRecorder() {
  const isRecording = ref(false)
  const elapsed = ref(0) // seconds

  let _timer = null

  /** Bắt đầu / dừng ghi âm */
  function toggle() {
    if (isRecording.value) {
      _stopTimer()
      isRecording.value = false
    } else {
      isRecording.value = true
      _startTimer()
    }
  }

  /** Reset timer và trạng thái */
  function reset() {
    _stopTimer()
    isRecording.value = false
    elapsed.value = 0
  }

  /** Format elapsed thành MM:SS */
  function formatTime(seconds) {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0')
    const s = (seconds % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  function _startTimer() {
    _timer = setInterval(() => { elapsed.value++ }, 1000)
  }

  function _stopTimer() {
    if (_timer) {
      clearInterval(_timer)
      _timer = null
    }
  }

  // Cleanup khi component unmount
  onUnmounted(_stopTimer)

  return { isRecording, elapsed, toggle, reset, formatTime }
}

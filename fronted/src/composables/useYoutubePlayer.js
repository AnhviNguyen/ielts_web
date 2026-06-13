/**
 * YouTube IFrame API — segment playback, auto-pause, speed control.
 */
import { ref, shallowRef, onUnmounted } from 'vue'

let apiPromise = null

function loadYoutubeApi() {
  if (window.YT?.Player) return Promise.resolve()
  if (!apiPromise) {
    apiPromise = new Promise((resolve) => {
      const prev = window.onYouTubeIframeAPIReady
      window.onYouTubeIframeAPIReady = () => {
        prev?.()
        resolve()
      }
      if (!document.querySelector('script[src*="youtube.com/iframe_api"]')) {
        const tag = document.createElement('script')
        tag.src = 'https://www.youtube.com/iframe_api'
        document.head.appendChild(tag)
      }
    })
  }
  return apiPromise
}

export function useYoutubePlayer() {
  const ready = ref(false)
  const playing = ref(false)
  const player = shallowRef(null)
  const pollId = ref(null)

  async function mount(el, videoId, { onStateChange, onTimeUpdate } = {}) {
    await loadYoutubeApi()
    if (player.value) {
      try { player.value.destroy() } catch { /* */ }
      player.value = null
    }

    player.value = new window.YT.Player(el, {
      videoId,
      width: '100%',
      height: '100%',
      playerVars: {
        rel: 0,
        modestbranding: 1,
        playsinline: 1,
        enablejsapi: 1,
        origin: typeof window !== 'undefined' ? window.location.origin : undefined,
      },
      events: {
        onReady: () => {
          ready.value = true
        },
        onStateChange: (e) => {
          playing.value = e.data === window.YT.PlayerState.PLAYING
          onStateChange?.(e)
        },
      },
    })

    stopPoll()
    pollId.value = window.setInterval(() => {
      if (!player.value?.getCurrentTime) return
      const t = player.value.getCurrentTime()
      onTimeUpdate?.(t)
    }, 100)
  }

  function stopPoll() {
    if (pollId.value) {
      clearInterval(pollId.value)
      pollId.value = null
    }
  }

  function seekTo(seconds) {
    player.value?.seekTo?.(seconds, true)
  }

  function play() {
    player.value?.playVideo?.()
    playing.value = true
  }

  function pause() {
    player.value?.pauseVideo?.()
    playing.value = false
  }

  function setRate(rate) {
    player.value?.setPlaybackRate?.(rate)
  }

  function getCurrentTime() {
    return player.value?.getCurrentTime?.() ?? 0
  }

  function destroy() {
    stopPoll()
    try {
      player.value?.destroy?.()
    } catch { /* */ }
    player.value = null
    ready.value = false
    playing.value = false
  }

  onUnmounted(destroy)

  return {
    ready,
    playing,
    mount,
    seekTo,
    play,
    pause,
    setRate,
    getCurrentTime,
    destroy,
  }
}

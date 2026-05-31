/** TTS helper — browser Speech Synthesis for English. */

let _speakingMsgIdx = null

export function stopSpeaking() {
  window.speechSynthesis?.cancel()
  _speakingMsgIdx = null
}

export function isSpeakingMessage(idx) {
  return _speakingMsgIdx === idx
}

/**
 * Speak English text. Optional msgIdx tracks which bubble is playing.
 * Returns a promise that resolves when speech ends or fails.
 */
export function speakEnglish(text, rate = 0.88, msgIdx = null) {
  return new Promise((resolve) => {
    if (!text || !window.speechSynthesis) {
      resolve(false)
      return
    }
    const utt = new SpeechSynthesisUtterance(text)
    utt.lang = 'en-US'
    utt.rate = rate
    _speakingMsgIdx = msgIdx

    const done = () => {
      if (_speakingMsgIdx === msgIdx) _speakingMsgIdx = null
      resolve(true)
    }
    utt.onend = done
    utt.onerror = done

    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utt)
  })
}

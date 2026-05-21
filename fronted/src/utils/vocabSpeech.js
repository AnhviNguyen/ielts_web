/** TTS helper — single responsibility. */
export function speakEnglish(text, rate = 0.88) {
  if (!text || !window.speechSynthesis) return
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = 'en-US'
  utt.rate = rate
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(utt)
}

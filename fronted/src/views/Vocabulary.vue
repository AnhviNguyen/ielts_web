<template>
  <div>
    <!-- Mode selection -->
    <div class="mode-grid">
      <div
        v-for="mode in modes"
        :key="mode.id"
        class="mode-card"
        :class="{ active: activeMode === mode.id }"
        @click="activeMode = mode.id"
      >
        <div class="mode-icon">{{ mode.icon }}</div>
        <div class="mode-name font-display">{{ mode.name }}</div>
        <div class="mode-desc">{{ mode.desc }}</div>
      </div>
    </div>

    <!-- Flashcard mode -->
    <div v-if="activeMode === 'flashcard'">
      <div class="fc-progress">
        <span class="fc-count font-mono">{{ fc.currentIndex.value + 1 }} / {{ fc.total.value }}</span>
        <div class="fc-bar">
          <div class="fc-bar-fill" :style="{ width: ((fc.currentIndex.value + 1) / fc.total.value * 100) + '%' }"></div>
        </div>
      </div>

      <!-- 3D Flashcard -->
      <div class="flashcard-container" style="height: 240px; margin: 20px 0;" @click="fc.flip()">
        <div class="flashcard-inner" :class="{ flipped: fc.isFlipped.value }">
          <div class="card-face card-front">
            <div class="card-word font-display">{{ fc.currentWord.value?.word }}</div>
            <div class="card-ipa font-mono">{{ fc.currentWord.value?.ipa }}</div>
            <button class="card-audio-btn" @click.stop>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            </button>
            <div class="card-hint-text">Bấm để xem nghĩa</div>
          </div>
          <div class="card-face card-back-face card-back-content">
            <div class="card-type-pill">{{ fc.currentWord.value?.type }}</div>
            <div class="card-meaning">{{ fc.currentWord.value?.meaning }}</div>
            <div class="card-example">{{ fc.currentWord.value?.example }}</div>
            <div v-if="fc.currentWord.value?.exampleVi" class="card-example-vi">{{ fc.currentWord.value?.exampleVi }}</div>
          </div>
        </div>
      </div>

      <!-- FSRS buttons -->
      <div class="fsrs-grid">
        <button class="fsrs-btn fsrs-again" @click="rate('again')">
          <span class="fsrs-emoji">😰</span>
          <span class="fsrs-label">Quên rồi</span>
          <span class="fsrs-next">Ôn lại: 1 ngày</span>
        </button>
        <button class="fsrs-btn fsrs-hard" @click="rate('hard')">
          <span class="fsrs-emoji">😓</span>
          <span class="fsrs-label">Khó</span>
          <span class="fsrs-next">Ôn lại: 3 ngày</span>
        </button>
        <button class="fsrs-btn fsrs-good" @click="rate('good')">
          <span class="fsrs-emoji">😊</span>
          <span class="fsrs-label">Ổn</span>
          <span class="fsrs-next">Ôn lại: 7 ngày</span>
        </button>
        <button class="fsrs-btn fsrs-easy" @click="rate('easy')">
          <span class="fsrs-emoji">🎉</span>
          <span class="fsrs-label">Dễ</span>
          <span class="fsrs-next">Ôn lại: 14 ngày</span>
        </button>
      </div>

      <!-- Word detail -->
      <div class="word-detail" v-if="fc.isFlipped.value && fc.currentWord.value">
        <div class="wd-row">
          <div>
            <div class="wd-word font-display">{{ fc.currentWord.value.word }}</div>
            <div class="wd-ipa font-mono">{{ fc.currentWord.value.ipa }}</div>
          </div>
          <div class="wd-type-badge">{{ fc.currentWord.value.type }}</div>
        </div>
        <div class="wd-section">
          <div class="wd-section-label">Từ liên quan</div>
          <div class="related-tags">
            <span v-for="w in fc.currentWord.value?.relatedWords" :key="w" class="related-tag">{{ w }}</span>
          </div>
        </div>
        <div class="wd-section">
          <div class="wd-section-label">Ví dụ trong context IELTS</div>
          <div class="wd-context">{{ fc.currentWord.value.example }}</div>
        </div>
      </div>
    </div>

    <!-- Match mode placeholder -->
    <div v-else-if="activeMode === 'match'" class="placeholder-mode">
      <div class="placeholder-icon">🃏</div>
      <div class="placeholder-title font-display">Ghép thẻ</div>
      <div class="placeholder-desc">Ghép từ với nghĩa trong thời gian ngắn nhất. Sắp ra mắt!</div>
    </div>

    <!-- Test mode placeholder -->
    <div v-else class="placeholder-mode">
      <div class="placeholder-icon">📝</div>
      <div class="placeholder-title font-display">Kiểm tra</div>
      <div class="placeholder-desc">Quiz nhiều dạng câu hỏi để kiểm tra vốn từ vựng. Sắp ra mắt!</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useVocabStore } from '@/stores/vocab.js'
import { useFlashcard } from '@/composables/useFlashcard.js'

const vocab = useVocabStore()
vocab.fetchWords()

const fc = useFlashcard(vocab.words)
const activeMode = ref('flashcard')

const modes = [
  { id: 'flashcard', name: 'Flashcard', icon: '🃏', desc: 'Ôn từ theo thuật toán FSRS' },
  { id: 'match',     name: 'Ghép thẻ', icon: '🔗', desc: 'Ghép từ với nghĩa tương ứng' },
  { id: 'test',      name: 'Kiểm tra', icon: '📝', desc: 'Quiz để kiểm tra vốn từ vựng' },
]

function rate(difficulty) {
  const interval = fc.rate(difficulty)
}
</script>

<style scoped>
.mode-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

.mode-card {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--r);
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.mode-card:hover { border-color: var(--violet-l); box-shadow: var(--shadow); }
.mode-card.active { border-color: var(--violet); background: var(--violet-bg); }

.mode-icon { font-size: 32px; margin-bottom: 10px; }
.mode-name { font-weight: 600; font-size: 15px; margin-bottom: 4px; color: var(--ink); }
.mode-desc { font-size: 11px; color: var(--ink3); line-height: 1.5; }

/* Progress */
.fc-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.fc-count { font-size: 12px; color: var(--ink3); white-space: nowrap; }

.fc-bar {
  flex: 1;
  height: 4px;
  background: var(--bg2);
  border-radius: 99px;
  overflow: hidden;
}

.fc-bar-fill {
  height: 100%;
  background: var(--violet-l);
  border-radius: 99px;
  transition: width 0.3s ease;
}

/* Flashcard 3D */
.flashcard-container { perspective: 1200px; cursor: pointer; }

.flashcard-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.flashcard-inner.flipped { transform: rotateY(180deg); }

.card-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  border-radius: var(--r);
  overflow: hidden;
}

.card-front {
  background: var(--ink);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
}

.card-word { font-size: 36px; font-weight: 700; color: white; margin-bottom: 8px; }
.card-ipa { font-size: 14px; color: var(--green-l); margin-bottom: 12px; }

.card-audio-btn {
  width: 40px; height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.12);
  border: none; color: white; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s;
}
.card-audio-btn:hover { background: rgba(255,255,255,0.25); }

.card-hint-text {
  position: absolute; bottom: 12px;
  font-size: 11px; color: rgba(255,255,255,0.3);
}

.card-back-face { transform: rotateY(180deg); }
.card-back-content {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 24px;
  display: flex; flex-direction: column; justify-content: center;
}

.card-type-pill {
  display: inline-block;
  padding: 2px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 600;
  background: var(--violet-bg); color: var(--violet);
  margin-bottom: 10px; align-self: flex-start;
}

.card-meaning { font-size: 18px; font-weight: 600; color: var(--ink); margin-bottom: 10px; line-height: 1.4; }
.card-example { font-size: 13px; color: var(--ink3); line-height: 1.6; font-style: italic; border-left: 3px solid var(--green-l); padding-left: 10px; }
.card-example-vi { font-size: 12px; color: var(--ink3); margin-top: 6px; padding-left: 13px; }

/* FSRS */
.fsrs-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }

.fsrs-btn {
  padding: 10px;
  border-radius: var(--r-sm);
  border: 1.5px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  font-family: inherit;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}

.fsrs-btn:hover { transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.fsrs-again { border-color: var(--rose-l); }
.fsrs-hard  { border-color: var(--amber-l); }
.fsrs-good  { border-color: var(--green-l); }
.fsrs-easy  { border-color: var(--blue-l); }

.fsrs-emoji { font-size: 20px; }
.fsrs-label { font-size: 11px; font-weight: 700; color: var(--ink); }
.fsrs-next  { font-size: 10px; color: var(--ink3); }

/* Word detail */
.word-detail {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 20px;
}

.wd-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.wd-word { font-size: 28px; font-weight: 700; color: var(--ink); }
.wd-ipa { font-size: 13px; color: var(--ink3); margin-top: 4px; }
.wd-type-badge { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: var(--violet-bg); color: var(--violet); }

.wd-section { margin-top: 14px; }
.wd-section-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink3); margin-bottom: 6px; }

.related-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.related-tag { padding: 4px 10px; border-radius: 20px; background: var(--bg2); border: 1px solid var(--border2); font-size: 12px; color: var(--ink2); }

.wd-context { font-size: 13px; color: var(--ink2); line-height: 1.7; background: var(--bg2); padding: 10px 14px; border-radius: var(--r-sm); border-left: 3px solid var(--green-l); }

/* Placeholder modes */
.placeholder-mode {
  text-align: center;
  padding: 60px 20px;
  background: var(--surface);
  border: 2px dashed var(--border2);
  border-radius: var(--r);
}
.placeholder-icon { font-size: 48px; margin-bottom: 16px; }
.placeholder-title { font-size: 20px; font-weight: 600; color: var(--ink); margin-bottom: 8px; }
.placeholder-desc { font-size: 13px; color: var(--ink3); }
</style>

<template>
  <Teleport to="body">
    <Transition name="badge-celebrate">
      <div
        v-if="celebration.active"
        class="badge-celebrate-overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="badge-celebrate-title"
        @click.self="celebration.dismiss()"
      >
        <div class="badge-celebrate-confetti" aria-hidden="true">
          <span v-for="n in 48" :key="n" class="confetti-piece" :style="pieceStyle(n)" />
        </div>

        <div class="badge-celebrate-card">
          <div class="badge-celebrate-glow" aria-hidden="true" />
          <p class="badge-celebrate-kicker">Chúc mừng!</p>
          <h2 id="badge-celebrate-title" class="badge-celebrate-title font-display">
            Huy hiệu mới
          </h2>
          <div class="badge-celebrate-icon" aria-hidden="true">
            <BadgeIcon :name="celebration.active?.icon || 'award'" :size="56" color="#059669" />
          </div>
          <h3 class="badge-celebrate-name">{{ celebration.active?.title }}</h3>
          <p class="badge-celebrate-desc">{{ celebration.active?.description }}</p>
          <button type="button" class="btn btn-primary badge-celebrate-btn" @click="celebration.dismiss()">
            Tuyệt vời!
          </button>
          <p v-if="celebration.queue.length" class="badge-celebrate-more">
            +{{ celebration.queue.length }} huy hiệu nữa đang chờ
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useBadgeCelebrationStore } from '@/stores/badgeCelebration.js'
import BadgeIcon from '@/components/ui/BadgeIcon.vue'

const celebration = useBadgeCelebrationStore()

const palette = ['#34d399', '#fbbf24', '#60a5fa', '#f472b6', '#a78bfa', '#fb923c']

function pieceStyle(n) {
  const left = ((n * 17) % 100)
  const delay = ((n * 7) % 20) / 10
  const dur = 2.2 + ((n * 3) % 10) / 10
  const color = palette[n % palette.length]
  const rot = (n * 41) % 360
  return {
    left: `${left}%`,
    backgroundColor: color,
    animationDelay: `${delay}s`,
    animationDuration: `${dur}s`,
    transform: `rotate(${rot}deg)`,
  }
}
</script>

<style scoped>
.badge-celebrate-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(4px);
}

.badge-celebrate-confetti {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.confetti-piece {
  position: absolute;
  top: -12px;
  width: 10px;
  height: 14px;
  border-radius: 2px;
  opacity: 0.9;
  animation-name: confetti-fall;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
}

@keyframes confetti-fall {
  0% {
    transform: translateY(-10vh) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(110vh) rotate(720deg);
    opacity: 0.35;
  }
}

.badge-celebrate-card {
  position: relative;
  width: min(100%, 380px);
  padding: 32px 28px 28px;
  text-align: center;
  background: #fff;
  border-radius: 20px;
  box-shadow:
    0 24px 60px rgba(15, 23, 42, 0.2),
    0 0 0 1px rgba(52, 211, 153, 0.25);
  animation: badge-pop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.badge-celebrate-glow {
  position: absolute;
  inset: -40px;
  background: radial-gradient(circle at 50% 30%, rgba(52, 211, 153, 0.35), transparent 65%);
  pointer-events: none;
  z-index: -1;
}

.badge-celebrate-kicker {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #059669;
}

.badge-celebrate-title {
  margin: 0 0 16px;
  font-size: 22px;
  color: var(--ink, #0f172a);
}

.badge-celebrate-icon {
  font-size: 56px;
  line-height: 1;
  margin-bottom: 12px;
  animation: badge-bounce 1.2s ease-in-out infinite;
}

.badge-celebrate-name {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--ink, #0f172a);
}

.badge-celebrate-desc {
  margin: 0 0 20px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ink3, #64748b);
}

.badge-celebrate-btn {
  min-width: 140px;
}

.badge-celebrate-more {
  margin: 12px 0 0;
  font-size: 11px;
  color: var(--ink3, #64748b);
}

@keyframes badge-pop {
  from {
    opacity: 0;
    transform: scale(0.85) translateY(12px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes badge-bounce {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-6px) scale(1.06); }
}

.badge-celebrate-enter-active,
.badge-celebrate-leave-active {
  transition: opacity 0.25s ease;
}

.badge-celebrate-enter-from,
.badge-celebrate-leave-to {
  opacity: 0;
}
</style>

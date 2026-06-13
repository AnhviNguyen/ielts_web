<template>
  <div class="hub-page">
    <section class="section-compact">
      <div class="app-container writing-hub">
        <div class="spotify-panel">
          <div class="spotify-panel__header text-center">
            <h1 class="font-display">Luyện Viết</h1>
            <p class="page-subtitle">Chọn hình thức luyện tập phù hợp với mục tiêu của bạn</p>
          </div>
          <div class="hub-card-stack">
            <article class="hub-card hub-card--primary" @click="$router.push('/writing/translation')">
              <div class="hub-card__left">
                <div class="hub-card__icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/>
                  </svg>
                </div>
                <div>
                  <h2 class="hub-card__title">Luyện dịch IELTS</h2>
                  <p class="hub-card__desc">Học idea, phương pháp viết bài, collocation tối ưu. Từng bước từ cơ bản đến Band 8.0+.</p>
                </div>
              </div>
              <button type="button" class="hub-card__btn hub-card__btn--primary">
                Khám phá
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
              </button>
            </article>
            <article class="hub-card hub-card--secondary" @click="$router.push('/writing/ielts')">
              <div class="hub-card__left">
                <div class="hub-card__icon hub-card__icon--alt">
                  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </div>
                <div>
                  <h2 class="hub-card__title hub-card__title--alt">Luyện viết IELTS</h2>
                  <p class="hub-card__desc hub-card__desc--alt">Kho câu hỏi khổng lồ từ các đề thi thật. Viết bài và được AI chấm chữa.</p>
                </div>
              </div>
              <button type="button" class="hub-card__btn hub-card__btn--alt">
                Khám phá
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
              </button>
            </article>
          </div>
        </div>
      </div>
    </section>
    <AiKeyRequiredModal :open="showGate" @close="goBack" @profile="goToProfile" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAiKeyGate } from '@/composables/useAiKeyGate.js'
import AiKeyRequiredModal from '@/components/ui/AiKeyRequiredModal.vue'

const { showGate, checkAiKey, goToProfile, goBack } = useAiKeyGate()

onMounted(() => checkAiKey())
</script>

<style scoped>
.writing-hub {
  max-width: 720px;
  margin: 0 auto;
}

.hub-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border-radius: 14px;
  padding: 22px 24px;
  cursor: pointer;
  transition: transform var(--transition-base), box-shadow var(--transition-base), border-color var(--transition-base);
}

.hub-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.hub-card--primary {
  background: var(--spotify-green-dark);
  border: 1.5px solid var(--spotify-green);
}

.hub-card--secondary {
  background: var(--bg-interactive);
  border: 1.5px solid var(--border-button);
}

.hub-card__left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.hub-card__icon {
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
}

.hub-card__icon--alt {
  background: var(--bg-surface);
  color: var(--ink);
}

.hub-card__title {
  font-size: var(--text-feature);
  font-weight: 700;
  color: #000;
  margin-bottom: 4px;
}

.hub-card__title--alt { color: var(--ink); }

.hub-card__desc {
  font-size: var(--text-caption);
  color: rgba(0, 0, 0, 0.72);
  line-height: 1.45;
}

.hub-card__desc--alt { color: var(--ink2); }

.hub-card__btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 18px;
  border-radius: var(--radius-large);
  font-weight: 600;
  font-size: var(--text-button);
  cursor: pointer;
  transition: var(--transition-base);
  white-space: nowrap;
}

.hub-card__btn--primary {
  border: 1.5px solid rgba(0, 0, 0, 0.35);
  background: rgba(0, 0, 0, 0.08);
  color: #000;
}

.hub-card__btn--primary:hover {
  background: rgba(0, 0, 0, 0.14);
}

.hub-card__btn--alt {
  border: 1.5px solid var(--border-button);
  color: var(--ink);
  background: var(--bg-surface);
}

.hub-card__btn--alt:hover {
  border-color: var(--spotify-green);
}

@media (max-width: 600px) {
  .hub-card {
    flex-direction: column;
    align-items: flex-start;
    padding: 18px 16px;
  }
  .hub-card__btn { width: 100%; justify-content: center; }
}
</style>

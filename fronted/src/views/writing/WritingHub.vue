<template>
  <div class="writing-hub">
    <div class="hub-header">
      <h1 class="hub-title">Luyện Viết</h1>
      <p class="hub-subtitle">Chọn hình thức luyện tập phù hợp với mục tiêu của bạn</p>
    </div>

    <div class="hub-cards">
      <!-- Translation Practice -->
      <article class="hub-card hub-card--primary" @click="$router.push('/writing/translation')">
        <div class="hub-card__left">
          <div class="hub-card__icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/>
            </svg>
          </div>
          <div>
            <h2 class="hub-card__title">Luyện dịch IELTS</h2>
            <p class="hub-card__desc">
              Học idea, phương pháp viết bài, collocation một cách tối ưu nhất.
              Từng bước từ cơ bản đến Band 8.0+.
            </p>
          </div>
        </div>
        <button class="hub-card__btn">
          Khám phá
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 8l4 4m0 0l-4 4m4-4H3"/>
          </svg>
        </button>
      </article>

      <!-- IELTS Writing Practice -->
      <article class="hub-card hub-card--secondary" @click="$router.push('/writing/ielts')">
        <div class="hub-card__left">
          <div class="hub-card__icon hub-card__icon--dark">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </div>
          <div>
            <h2 class="hub-card__title hub-card__title--light">Luyện viết IELTS</h2>
            <p class="hub-card__desc hub-card__desc--light">
              Kho câu hỏi khổng lồ từ các đề thi thật. Viết bài và được AI chấm chữa.
            </p>
          </div>
        </div>
        <button class="hub-card__btn hub-card__btn--light">
          Khám phá
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 8l4 4m0 0l-4 4m4-4H3"/>
          </svg>
        </button>
      </article>
    </div>
  </div>
</template>

<script setup>
// No state needed — purely navigational
</script>

<style scoped>
.writing-hub {
  max-width: 720px;
  margin: 0 auto;
  padding: 56px 24px;
}

.hub-header {
  text-align: center;
  margin-bottom: 44px;
}

.hub-title {
  font-size: 2rem;
  font-weight: 800;
  color: #111;
  margin-bottom: 8px;
}

.hub-subtitle {
  font-size: 1rem;
  color: #6b7280;
}

.hub-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Card base */
.hub-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border-radius: 18px;
  padding: 28px 32px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hub-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

.hub-card--primary {
  background: #064e3b;
  border: 1.5px solid #34d399;
}

.hub-card--secondary {
  background: #fff;
  border: 1.5px solid #e5e7eb;
}

.hub-card__left {
  display: flex;
  align-items: center;
  gap: 18px;
  flex: 1;
  min-width: 0;
}

.hub-card__icon {
  flex-shrink: 0;
  width: 54px;
  height: 54px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.hub-card__icon--dark {
  background: #f3f4f6;
  color: #111;
}

.hub-card__title {
  font-size: 1.2rem;
  font-weight: 800;
  color: #fff;
  margin-bottom: 6px;
}

.hub-card__title--light { color: #111; }

.hub-card__desc {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

.hub-card__desc--light { color: #6b7280; }

.hub-card__btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 30px;
  font-weight: 700;
  font-size: 0.875rem;
  border: 1.5px solid rgba(255, 255, 255, 0.4);
  cursor: pointer;
  background: transparent;
  color: #fff;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.hub-card__btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.7);
}

.hub-card__btn--light {
  border-color: #e5e7eb;
  color: #111;
  background: #f9fafb;
}

.hub-card__btn--light:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

@media (max-width: 600px) {
  .hub-card {
    flex-direction: column;
    align-items: flex-start;
    padding: 22px 20px;
  }

  .hub-card__btn { width: 100%; justify-content: center; }
}
</style>

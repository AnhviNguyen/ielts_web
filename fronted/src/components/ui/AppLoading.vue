<template>
  <div class="app-loading" :class="{ 'app-loading--inline': inline }" role="status" aria-label="Đang tải">
    <img src="/loading.svg" alt="" class="app-loading__img" :style="{ width: size + 'px', height: size + 'px' }" />
    <p v-if="message" class="app-loading__msg">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: '' },
  size: { type: Number, default: 48 },
  inline: { type: Boolean, default: false },
})
</script>

<style scoped>
.app-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
}
.app-loading--inline {
  padding: 12px;
}
.app-loading__img {
  display: block;
}
.app-loading__msg {
  margin: 0;
  font-size: 13px;
  color: var(--ink3);
}
</style>

<template>
  <div class="grid grid-cols-2 gap-3">
    <button
      type="button"
      class="rounded-[var(--r)] border-2 border-[var(--border)] bg-[var(--bg)] p-5 text-center transition-colors hover:border-[var(--green-l)] hover:bg-[var(--green-bg)]"
      @click="$emit('select', 'practice')"
    >
      <div class="mb-2 text-3xl">📖</div>
      <div class="text-sm font-bold text-[var(--ink)]">Luyện tập</div>
      <div class="mt-1 text-[11px] text-[var(--ink3)]">Tự do, không giới hạn thời gian</div>
    </button>
    <button
      type="button"
      class="rounded-[var(--r)] border-2 border-[var(--border)] bg-[var(--bg)] p-5 text-center transition-colors hover:border-[var(--green-l)] hover:bg-[var(--green-bg)]"
      @click="$emit('select', 'exam')"
    >
      <div class="mb-2 text-3xl">⏱️</div>
      <div class="text-sm font-bold text-[var(--ink)]">Thi thật</div>
      <div class="mt-1 text-[11px] text-[var(--ink3)]">Giới hạn 20 phút như thi thật</div>
    </button>
  </div>
</template>

<script setup>
defineEmits(['select'])
</script>

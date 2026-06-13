<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[600] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      <div class="absolute inset-0 bg-black/45" @click="$emit('close')" />
      <div class="relative z-10 w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)] p-6 shadow-xl">
        <div class="mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--amber-bg)] text-[var(--amber)]">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4"/><path d="M12 18v4"/><path d="m4.93 4.93 2.83 2.83"/><path d="m16.24 16.24 2.83 2.83"/>
            <path d="M2 12h4"/><path d="M18 12h4"/><path d="m4.93 19.07 2.83-2.83"/><path d="m16.24 7.76 2.83-2.83"/>
          </svg>
        </div>
        <h2 class="font-display text-lg font-bold text-[var(--ink)]">Cần cấu hình API key</h2>
        <p class="mt-2 text-[13px] leading-relaxed text-[var(--ink2)]">
          Tính năng này dùng AI để chấm bài / hội thoại / dịch. Vui lòng vào
          <strong>Profile → Cài đặt API key</strong> và thêm
          <strong>OpenRouter API key</strong> cá nhân (lấy tại openrouter.ai/keys).
        </p>
        <div class="mt-5 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button type="button" class="ct-btn text-[12px]" @click="$emit('close')">Quay lại</button>
          <button type="button" class="ct-btn bg-[var(--spotify-green)] text-black border-transparent text-[12px] font-semibold" @click="$emit('profile')">
            Đến Profile
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
})
defineEmits(['close', 'profile'])
</script>

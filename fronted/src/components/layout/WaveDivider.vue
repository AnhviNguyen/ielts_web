<template>
  <div class="wave-divider" aria-hidden="true">
    <svg viewBox="0 0 1200 48" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M0,24 C300,48 600,0 900,24 C1050,36 1150,12 1200,24 L1200,48 L0,48 Z"
        :fill="fill"
      />
    </svg>
  </div>
</template>

<script setup>
defineProps({
  /** CSS color for the wave fill — should match the next section background */
  fill: { type: String, default: 'var(--section-white)' },
})
</script>

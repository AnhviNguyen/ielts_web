<template>
  <img
    :src="resolvedSrc"
    :alt="alt"
    :referrerpolicy="needsNoReferrer ? 'no-referrer' : undefined"
    @error="onError"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { avatarUrl, DEFAULT_AVATAR, isExternalAvatar } from '@/utils/mediaUrl.js'

const props = defineProps({
  url: { type: String, default: '' },
  alt: { type: String, default: '' },
})

const failed = ref(false)

const resolvedSrc = computed(() => (failed.value ? DEFAULT_AVATAR : avatarUrl(props.url)))
const needsNoReferrer = computed(() => !failed.value && isExternalAvatar(props.url))

watch(() => props.url, () => {
  failed.value = false
})

function onError() {
  failed.value = true
}
</script>

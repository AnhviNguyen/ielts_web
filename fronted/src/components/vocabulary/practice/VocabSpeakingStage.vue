<template>
  <WordPronunciationCard
    :word="word.word"
    :meaning-vi="word.meaning_vi || ''"
    :result="result"
    :reviewing="reviewing"
    @speak="$emit('speak')"
    @scored="$emit('scored', $event)"
    @retry="$emit('retry')"
    @next="$emit('next')"
  />
</template>

<script setup>
import WordPronunciationCard from '@/components/WordPronunciationCard.vue'

defineProps({
  word: { type: Object, required: true },
  result: { type: String, default: null },
  reviewing: Boolean,
})

defineEmits(['speak', 'scored', 'next', 'retry'])
</script>

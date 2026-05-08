<template>
  <div ref="rootEl" class="gap-html prose max-w-none leading-relaxed"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  html:     { type: String,  default: '' },
  gaps:     { type: Object,  default: () => ({}) }, // { gf_1: { questionId, value } }
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['answer'])

const rootEl = ref(null)

// ── Build the full HTML string (structure + initial values) ──────────
function buildHtml() {
  let counter = 0
  return (props.html || '').replace(
    /<span[^>]*class="gap-placeholder"[^>]*data-question-id="([^"]+)"[^>]*>[\s\S]*?<\/span>/g,
    (_m, gapKey) => {
      counter++
      const q = props.gaps?.[gapKey]
      const v = (q?.value ?? '').replace(/"/g, '&quot;')
      const dis = props.disabled ? 'disabled' : ''
      // Numbered badge + underline input (no border box)
      return `<span class="gap-wrapper" data-gap-key="${gapKey}">`
           + `<span class="gap-num">${counter}</span>`
           + `<input ${dis} type="text" data-gap-key="${gapKey}" value="${v}" class="gap-input" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" />`
           + `</span>`
    }
  )
}

// ── Only re-render DOM when structure changes (html or gap keys) ─────
function buildStructureKey() {
  return props.html + '|' + Object.keys(props.gaps || {}).join(',') + '|' + props.disabled
}

let lastStructureKey = ''
function renderIfNeeded() {
  const key = buildStructureKey()
  if (key === lastStructureKey) return
  lastStructureKey = key
  if (!rootEl.value) return
  rootEl.value.innerHTML = buildHtml()
  // restore values after rebuild
  syncValues()
}

// ── Sync only input values (no DOM rebuild) ──────────────────────────
function syncValues() {
  if (!rootEl.value) return
  rootEl.value.querySelectorAll('.gap-input').forEach(input => {
    const gapKey = input.dataset.gapKey
    const q = props.gaps?.[gapKey]
    const v = String(q?.value ?? '')
    if (input.value !== v && document.activeElement !== input) {
      input.value = v
    }
  })
}

watch(
  () => buildStructureKey(),
  () => renderIfNeeded()
)

watch(
  () => props.gaps,
  () => syncValues(),
  { deep: true }
)

// ── Capture input events from dynamic inputs ─────────────────────────
function onInput(e) {
  const el = e.target
  if (!rootEl.value?.contains(el) || !el.classList.contains('gap-input')) return
  const gapKey = el.dataset.gapKey
  if (!gapKey) return
  emit('answer', { gapKey, value: el.value })
}

onMounted(() => {
  renderIfNeeded()
  window.addEventListener('input', onInput, true)
})
onUnmounted(() => window.removeEventListener('input', onInput, true))
</script>

<style>
/* Cathoven-style underline input */
.gap-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  vertical-align: baseline;
}

.gap-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #34d399;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  vertical-align: middle;
  flex-shrink: 0;
}

.gap-input {
  display: inline-block;
  min-width: 88px;
  max-width: 160px;
  padding: 1px 4px 2px;
  border: none;
  border-bottom: 2px solid #111;
  border-radius: 0;
  background: transparent;
  color: #111;
  font: inherit;
  font-size: 14px;
  outline: none;
  vertical-align: baseline;
  transition: border-color 0.12s;
}
.gap-input:focus {
  border-bottom-color: #34d399;
}
.gap-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

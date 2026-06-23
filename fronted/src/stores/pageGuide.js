import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { PAGE_TOURS } from '@/config/pageTours.js'
import { hasSeenPageGuide, markPageGuideSeen } from '@/utils/pageGuideStorage.js'

export const usePageGuideStore = defineStore('pageGuide', () => {
  const visible = ref(false)
  const activeKey = ref(null)
  const stepIndex = ref(0)
  const manualOpen = ref(false)
  let pendingTimer = null

  const tour = computed(() => (activeKey.value ? PAGE_TOURS[activeKey.value] : null))
  const totalSteps = computed(() => tour.value?.steps?.length ?? 0)
  const currentStep = computed(() => tour.value?.steps?.[stepIndex.value] ?? null)

  function cancelPending() {
    if (pendingTimer) {
      clearTimeout(pendingTimer)
      pendingTimer = null
    }
  }

  function dismiss() {
    visible.value = false
    activeKey.value = null
    stepIndex.value = 0
    manualOpen.value = false
  }

  function finish(userScope) {
    if (!manualOpen.value && activeKey.value) {
      markPageGuideSeen(userScope, activeKey.value)
    }
    dismiss()
  }

  function nextStep() {
    if (stepIndex.value < totalSteps.value - 1) stepIndex.value += 1
  }

  function prevStep() {
    if (stepIndex.value > 0) stepIndex.value -= 1
  }

  function startTour(guideKey, manual = false) {
    if (!PAGE_TOURS[guideKey]) return
    cancelPending()
    manualOpen.value = manual
    activeKey.value = guideKey
    stepIndex.value = 0
    visible.value = true
  }

  function tryShow(guideKey, userScope, { delayMs = 600 } = {}) {
    cancelPending()
    if (!guideKey || !PAGE_TOURS[guideKey]) return
    if (hasSeenPageGuide(userScope, guideKey)) return

    pendingTimer = setTimeout(() => {
      pendingTimer = null
      if (hasSeenPageGuide(userScope, guideKey)) return
      startTour(guideKey, false)
    }, delayMs)
  }

  function openManual(guideKey) {
    if (!PAGE_TOURS[guideKey]) return
    startTour(guideKey, true)
  }

  return {
    visible,
    activeKey,
    stepIndex,
    manualOpen,
    totalSteps,
    currentStep,
    tour,
    tryShow,
    openManual,
    finish,
    dismiss,
    nextStep,
    prevStep,
    cancelPending,
  }
})

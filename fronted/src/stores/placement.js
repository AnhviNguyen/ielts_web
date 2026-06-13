import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  createPlacementSession,
  finalizeFullExamPlacement,
  finalizePlacement,
  getPlacementStage,
  getPlacementStatus,
  submitManualPlacement,
  submitPlacementStage,
} from '@/services/placementService.js'

export const usePlacementStore = defineStore('placement', () => {
  const status = ref(null)
  const session = ref(null)
  const stage = ref(null)
  const loading = ref(false)
  const error = ref('')
  const modalOpen = ref(false)

  const needsPlacement = computed(() => (status.value?.placement_status || 'pending') !== 'completed')

  function openModal() {
    modalOpen.value = true
  }

  function closeModal() {
    modalOpen.value = false
  }

  async function loadStatus() {
    try {
      status.value = await getPlacementStatus()
      return status.value
    } catch {
      status.value = null
      return null
    }
  }

  async function submitManual(body) {
    loading.value = true
    error.value = ''
    try {
      const result = await submitManualPlacement(body)
      await loadStatus()
      return result
    } catch (err) {
      error.value = err.response?.data?.detail || 'Cannot save placement scores.'
      return null
    } finally {
      loading.value = false
    }
  }

  async function startDiagnostic() {
    loading.value = true
    error.value = ''
    try {
      session.value = await createPlacementSession()
      await loadStage(session.value.current_stage || 'reading')
      return session.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Cannot start diagnostic.'
      return null
    } finally {
      loading.value = false
    }
  }

  async function loadStage(stageName) {
    if (!session.value?.id) return null
    loading.value = true
    error.value = ''
    try {
      stage.value = await getPlacementStage(session.value.id, stageName)
      session.value = stage.value.session
      return stage.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Cannot load diagnostic stage.'
      return null
    } finally {
      loading.value = false
    }
  }

  async function submitStage(stageName, body) {
    if (!session.value?.id) return null
    loading.value = true
    error.value = ''
    try {
      const result = await submitPlacementStage(session.value.id, stageName, body)
      session.value = result.session
      if (result.session.current_stage === 'review') {
        stage.value = null
      } else {
        await loadStage(result.session.current_stage)
      }
      return result
    } catch (err) {
      error.value = err.response?.data?.detail || 'Cannot submit this stage.'
      return null
    } finally {
      loading.value = false
    }
  }

  async function finalize() {
    if (!session.value?.id) return null
    loading.value = true
    error.value = ''
    try {
      const result = await finalizePlacement(session.value.id)
      await loadStatus()
      return result
    } catch (err) {
      error.value = err.response?.data?.detail || 'Cannot finalize diagnostic.'
      return null
    } finally {
      loading.value = false
    }
  }

  async function finalizeFullExam(body) {
    loading.value = true
    error.value = ''
    try {
      const result = await finalizeFullExamPlacement(body)
      await loadStatus()
      return result
    } catch (err) {
      error.value = err.response?.data?.detail || 'Cannot finalize full exam placement.'
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    status,
    session,
    stage,
    loading,
    error,
    modalOpen,
    needsPlacement,
    openModal,
    closeModal,
    loadStatus,
    submitManual,
    startDiagnostic,
    loadStage,
    submitStage,
    finalize,
    finalizeFullExam,
  }
})

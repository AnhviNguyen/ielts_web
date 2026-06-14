/**
 * src/stores/__tests__/placement.spec.js
 * ────────────────────────────────────────
 * Unit tests for the placement Pinia store.
 * Mocks all placement service functions to avoid real API calls.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePlacementStore } from '../placement.js'

// ── Module-level mocks ────────────────────────────────────────────────────────

const mockGetPlacementStatus = vi.fn()
const mockSubmitManualPlacement = vi.fn()
const mockFinalizeFullExamPlacement = vi.fn()
const mockCreatePlacementSession = vi.fn()
const mockGetPlacementStage = vi.fn()
const mockSubmitPlacementStage = vi.fn()
const mockFinalizePlacement = vi.fn()

vi.mock('@/services/placementService.js', () => ({
  getPlacementStatus: (...args) => mockGetPlacementStatus(...args),
  submitManualPlacement: (...args) => mockSubmitManualPlacement(...args),
  finalizeFullExamPlacement: (...args) => mockFinalizeFullExamPlacement(...args),
  createPlacementSession: (...args) => mockCreatePlacementSession(...args),
  getCurrentPlacementSession: vi.fn(),
  getPlacementStage: (...args) => mockGetPlacementStage(...args),
  submitPlacementStage: (...args) => mockSubmitPlacementStage(...args),
  finalizePlacement: (...args) => mockFinalizePlacement(...args),
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_PENDING = { placement_status: 'pending', initial_band: null }
const STATUS_COMPLETED = { placement_status: 'completed', initial_band: 6.0 }

const MOCK_SESSION = { id: 'sess-plc-001', current_stage: 'reading', status: 'in_progress' }
const MOCK_SESSION_LISTENING = { id: 'sess-plc-001', current_stage: 'listening', status: 'in_progress' }
const MOCK_SESSION_REVIEW = { id: 'sess-plc-001', current_stage: 'review', status: 'in_progress' }

const MOCK_READING_STAGE = {
  session: MOCK_SESSION,
  stage: 'reading',
  questions: [{ id: 'rq1' }, { id: 'rq2' }],
}

const MOCK_SUBMIT_READING = {
  session: MOCK_SESSION_LISTENING, // advance to listening
}

const MOCK_SUBMIT_FINAL = {
  session: MOCK_SESSION_REVIEW, // finalize → review
}

// ── Test Suite ────────────────────────────────────────────────────────────────

describe('usePlacementStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // ── PLA-01: needsPlacement computed ──────────────────────────────────────
  it('PLA-01: needsPlacement = true khi status là "pending"', async () => {
    mockGetPlacementStatus.mockResolvedValue(STATUS_PENDING)

    const store = usePlacementStore()
    await store.loadStatus()

    expect(store.needsPlacement).toBe(true)
  })

  // ── PLA-02: needsPlacement = false sau khi completed ─────────────────────
  it('PLA-02: needsPlacement = false khi placement_status là "completed"', async () => {
    mockGetPlacementStatus.mockResolvedValue(STATUS_COMPLETED)

    const store = usePlacementStore()
    await store.loadStatus()

    expect(store.needsPlacement).toBe(false)
  })

  // ── PLA-03: loadStatus — thất bại ────────────────────────────────────────
  it('PLA-03: loadStatus thất bại không crash, status = null', async () => {
    mockGetPlacementStatus.mockRejectedValue(new Error('Network error'))

    const store = usePlacementStore()
    const result = await store.loadStatus()

    expect(result).toBeNull()
    expect(store.status).toBeNull()
  })

  // ── PLA-04: openModal / closeModal ────────────────────────────────────────
  it('PLA-04: openModal và closeModal hoạt động đúng', () => {
    const store = usePlacementStore()
    expect(store.modalOpen).toBe(false)

    store.openModal()
    expect(store.modalOpen).toBe(true)

    store.closeModal()
    expect(store.modalOpen).toBe(false)
  })

  // ── PLA-05: startDiagnostic — happy path ─────────────────────────────────
  it('PLA-05: startDiagnostic khởi tạo session và tải stage đầu tiên', async () => {
    mockCreatePlacementSession.mockResolvedValue(MOCK_SESSION)
    mockGetPlacementStage.mockResolvedValue(MOCK_READING_STAGE)

    const store = usePlacementStore()
    const session = await store.startDiagnostic()

    expect(session).toEqual(MOCK_SESSION)
    expect(store.session).toEqual(MOCK_SESSION)
    expect(mockGetPlacementStage).toHaveBeenCalledWith('sess-plc-001', 'reading')
    expect(store.stage).toEqual(MOCK_READING_STAGE)
  })

  // ── PLA-06: startDiagnostic — thất bại ───────────────────────────────────
  it('PLA-06: startDiagnostic thất bại cập nhật error và trả về null', async () => {
    mockCreatePlacementSession.mockRejectedValue({
      response: { data: { detail: 'Session already exists' } },
    })

    const store = usePlacementStore()
    const result = await store.startDiagnostic()

    expect(result).toBeNull()
    expect(store.error).toBe('Session already exists')
  })

  // ── PLA-07: loadStage ────────────────────────────────────────────────────
  it('PLA-07: loadStage tải thông tin chặng thi và cập nhật session', async () => {
    mockCreatePlacementSession.mockResolvedValue(MOCK_SESSION)
    mockGetPlacementStage.mockResolvedValue(MOCK_READING_STAGE)

    const store = usePlacementStore()
    await store.startDiagnostic()
    // Reset mock for second call
    mockGetPlacementStage.mockClear()
    mockGetPlacementStage.mockResolvedValue({ session: MOCK_SESSION, stage: 'reading', questions: [] })

    await store.loadStage('reading')

    expect(mockGetPlacementStage).toHaveBeenCalledWith('sess-plc-001', 'reading')
  })

  // ── PLA-08: loadStage khi không có session ────────────────────────────────
  it('PLA-08: loadStage không làm gì nếu chưa có session', async () => {
    const store = usePlacementStore()
    const result = await store.loadStage('reading')

    expect(result).toBeNull()
    expect(mockGetPlacementStage).not.toHaveBeenCalled()
  })

  // ── PLA-09: submitStage — chuyển chặng tiếp theo ─────────────────────────
  it('PLA-09: submitStage nộp bài reading và tự động chuyển sang listening', async () => {
    mockCreatePlacementSession.mockResolvedValue(MOCK_SESSION)
    mockGetPlacementStage
      .mockResolvedValueOnce(MOCK_READING_STAGE) // initial load
      .mockResolvedValueOnce({ session: MOCK_SESSION_LISTENING, stage: 'listening', questions: [] }) // after submit

    mockSubmitPlacementStage.mockResolvedValue(MOCK_SUBMIT_READING)

    const store = usePlacementStore()
    await store.startDiagnostic()

    const result = await store.submitStage('reading', { answers: {} })

    expect(result).toEqual(MOCK_SUBMIT_READING)
    expect(store.session.current_stage).toBe('listening')
    expect(mockGetPlacementStage).toHaveBeenCalledWith('sess-plc-001', 'listening')
  })

  // ── PLA-10: submitStage — chặng cuối → review ────────────────────────────
  it('PLA-10: submitStage chặng cuối chuyển sang review và stage = null', async () => {
    mockCreatePlacementSession.mockResolvedValue(MOCK_SESSION)
    mockGetPlacementStage.mockResolvedValue(MOCK_READING_STAGE)
    mockSubmitPlacementStage.mockResolvedValue(MOCK_SUBMIT_FINAL)

    const store = usePlacementStore()
    await store.startDiagnostic()

    await store.submitStage('speaking', { answers: {} })

    expect(store.session.current_stage).toBe('review')
    expect(store.stage).toBeNull()
  })

  // ── PLA-11: finalize ─────────────────────────────────────────────────────
  it('PLA-11: finalize hoàn thành bài kiểm tra và reload status', async () => {
    mockCreatePlacementSession.mockResolvedValue(MOCK_SESSION)
    mockGetPlacementStage.mockResolvedValue(MOCK_READING_STAGE)
    mockFinalizePlacement.mockResolvedValue({ band: 6.0 })
    mockGetPlacementStatus.mockResolvedValue(STATUS_COMPLETED)

    const store = usePlacementStore()
    await store.startDiagnostic()

    const result = await store.finalize()

    expect(result).toEqual({ band: 6.0 })
    expect(mockFinalizePlacement).toHaveBeenCalledWith('sess-plc-001')
    expect(mockGetPlacementStatus).toHaveBeenCalled()
    expect(store.needsPlacement).toBe(false)
  })

  // ── PLA-12: submitManual ─────────────────────────────────────────────────
  it('PLA-12: submitManual gửi điểm thủ công và reload status', async () => {
    const manualBody = { reading: 7.0, listening: 6.5, writing: 6.0, speaking: 6.0 }
    mockSubmitManualPlacement.mockResolvedValue({ band: 6.5 })
    mockGetPlacementStatus.mockResolvedValue(STATUS_COMPLETED)

    const store = usePlacementStore()
    const result = await store.submitManual(manualBody)

    expect(result).toEqual({ band: 6.5 })
    expect(mockSubmitManualPlacement).toHaveBeenCalledWith(manualBody)
    expect(store.needsPlacement).toBe(false)
  })

  // ── PLA-13: finalizeFullExam ──────────────────────────────────────────────
  it('PLA-13: finalizeFullExam hoàn thành qua bài thi đầy đủ', async () => {
    const body = { full_exam_id: 'exam-001' }
    mockFinalizeFullExamPlacement.mockResolvedValue({ band: 7.0 })
    mockGetPlacementStatus.mockResolvedValue(STATUS_COMPLETED)

    const store = usePlacementStore()
    const result = await store.finalizeFullExam(body)

    expect(result).toEqual({ band: 7.0 })
    expect(mockFinalizeFullExamPlacement).toHaveBeenCalledWith(body)
    expect(store.needsPlacement).toBe(false)
  })
})

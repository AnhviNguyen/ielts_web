/**
 * src/stores/__tests__/practice.spec.js
 * ──────────────────────────────────────
 * Unit tests for the practice Pinia store.
 * Uses vi.hoisted() for mocks to avoid Vitest hoisting errors.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePracticeStore } from '../practice.js'

// ── Hoisted mocks ─────────────────────────────────────────────────────────────
const { mockPracticeService, mockEnqueue } = vi.hoisted(() => {
  return {
    mockPracticeService: {
      createReadingSession: vi.fn(),
      createListeningSession: vi.fn(),
      submitReading: vi.fn(),
      submitListening: vi.fn(),
      checkAnswer: vi.fn(),
      getResultBySession: vi.fn(),
      getResultByQuiz: vi.fn(),
    },
    mockEnqueue: vi.fn(),
  }
})

vi.mock('@/services/practiceService.js', () => ({
  practiceService: mockPracticeService,
}))

vi.mock('@/stores/badgeCelebration.js', () => ({
  useBadgeCelebrationStore: vi.fn(() => ({ enqueue: mockEnqueue })),
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

const MOCK_READING_SESSION = {
  session_id: 'sess-read-001',
  quiz_id: 'quiz-001',
  skill: 'reading',
  questions: [{ id: 'q1' }, { id: 'q2' }],
}

const MOCK_LISTENING_SESSION = {
  session_id: 'sess-listen-001',
  quiz_id: 'quiz-002',
  skill: 'listening',
  questions: [{ id: 'q3' }],
}

const MOCK_RESULT = {
  score: 35,
  band_score: 7.0,
  new_badges: [],
  correct_count: 35,
  total_questions: 40,
}

// ── Test Suite ────────────────────────────────────────────────────────────────

describe('usePracticeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // ── PR-01: startSession — Reading ────────────────────────────────────────
  it('PR-01: startSession("reading") tạo reading session thành công', async () => {
    mockPracticeService.createReadingSession.mockResolvedValue(MOCK_READING_SESSION)
    const store = usePracticeStore()
    const session = await store.startSession('reading')
    expect(session).toEqual(MOCK_READING_SESSION)
    expect(store.currentSession).toEqual(MOCK_READING_SESSION)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // ── PR-02: startSession — Listening ──────────────────────────────────────
  it('PR-02: startSession("listening") tạo listening session thành công', async () => {
    mockPracticeService.createListeningSession.mockResolvedValue(MOCK_LISTENING_SESSION)
    const store = usePracticeStore()
    const session = await store.startSession('listening')
    expect(session).toEqual(MOCK_LISTENING_SESSION)
    expect(mockPracticeService.createListeningSession).toHaveBeenCalledTimes(1)
  })

  // ── PR-03: startSession — với quizId cụ thể ──────────────────────────────
  it('PR-03: startSession truyền quizId đến service', async () => {
    mockPracticeService.createReadingSession.mockResolvedValue(MOCK_READING_SESSION)
    const store = usePracticeStore()
    await store.startSession('reading', 'quiz-specific-001')
    expect(mockPracticeService.createReadingSession).toHaveBeenCalledWith('quiz-specific-001')
  })

  // ── PR-04: startSession — thất bại ───────────────────────────────────────
  it('PR-04: startSession thất bại cập nhật error và trả về null', async () => {
    mockPracticeService.createReadingSession.mockRejectedValue({
      response: { data: { detail: 'No quiz available' } },
    })
    const store = usePracticeStore()
    const result = await store.startSession('reading')
    expect(result).toBeNull()
    expect(store.error).toBe('No quiz available')
  })

  // ── PR-05: submitSession — Reading thành công ────────────────────────────
  it('PR-05: submitSession("reading") nộp bài và lưu kết quả', async () => {
    mockPracticeService.submitReading.mockResolvedValue(MOCK_RESULT)
    const store = usePracticeStore()
    const result = await store.submitSession('reading', 'sess-read-001', { q1: 'A' })
    expect(result).toEqual(MOCK_RESULT)
    expect(store.lastResult).toEqual(MOCK_RESULT)
    expect(mockPracticeService.submitReading).toHaveBeenCalledTimes(1)
  })

  // ── PR-06: submitSession — Listening thành công ──────────────────────────
  it('PR-06: submitSession("listening") gọi đúng submitListening', async () => {
    mockPracticeService.submitListening.mockResolvedValue(MOCK_RESULT)
    const store = usePracticeStore()
    await store.submitSession('listening', 'sess-listen-001', {})
    expect(mockPracticeService.submitListening).toHaveBeenCalledTimes(1)
  })

  // ── PR-07: submitSession — enqueue badges ────────────────────────────────
  it('PR-07: submitSession đẩy new_badges vào badgeCelebrationStore', async () => {
    const resultWithBadges = { ...MOCK_RESULT, new_badges: [{ id: 'badge-1', name: 'First Practice' }] }
    mockPracticeService.submitReading.mockResolvedValue(resultWithBadges)
    const store = usePracticeStore()
    await store.submitSession('reading', 'sess-read-001', {})
    expect(mockEnqueue).toHaveBeenCalledWith(resultWithBadges.new_badges)
  })

  // ── PR-08: submitSession — đã submit trước đó ────────────────────────────
  it('PR-08: submitSession khi 400 "already submitted" thì tự fetch lại kết quả', async () => {
    mockPracticeService.submitReading.mockRejectedValue({
      response: { status: 400, data: { detail: 'Session already submitted' } },
    })
    mockPracticeService.getResultBySession.mockResolvedValue(MOCK_RESULT)
    const store = usePracticeStore()
    const result = await store.submitSession('reading', 'sess-read-001', {})
    expect(mockPracticeService.getResultBySession).toHaveBeenCalledWith('sess-read-001')
    expect(result).toEqual(MOCK_RESULT)
  })

  // ── PR-09: checkAnswer ────────────────────────────────────────────────────
  it('PR-09: checkAnswer trả về kết quả kiểm tra đúng/sai từ service', async () => {
    const mockCheckResult = { is_correct: true, correct_answer: 'B', explanation: 'B is correct.' }
    mockPracticeService.checkAnswer.mockResolvedValue(mockCheckResult)
    const store = usePracticeStore()
    const result = await store.checkAnswer('sess-001', 'q1', 'B')
    expect(result).toEqual(mockCheckResult)
    expect(mockPracticeService.checkAnswer).toHaveBeenCalledWith({
      session_id: 'sess-001',
      question_id: 'q1',
      user_answer: 'B',
    })
  })

  // ── PR-10: fetchResult — theo sessionId ──────────────────────────────────
  it('PR-10: fetchResult lấy kết quả theo session_id', async () => {
    const sessionPayload = { history: MOCK_RESULT }
    mockPracticeService.getResultBySession.mockResolvedValue(sessionPayload)
    const store = usePracticeStore()
    const result = await store.fetchResult('sess-read-001')
    expect(result).toEqual(MOCK_RESULT)
    expect(store.lastResult).toEqual(MOCK_RESULT)
  })

  // ── PR-11: fetchResultByQuiz ──────────────────────────────────────────────
  it('PR-11: fetchResultByQuiz lấy kết quả theo quiz_id', async () => {
    const quizPayload = { history: MOCK_RESULT }
    mockPracticeService.getResultByQuiz.mockResolvedValue(quizPayload)
    const store = usePracticeStore()
    const result = await store.fetchResultByQuiz('quiz-001')
    expect(result).toEqual(MOCK_RESULT)
  })

  // ── PR-12: đo thời gian duration_seconds ─────────────────────────────────
  it('PR-12: submitSession bao gồm duration_seconds >= 0 sau startSession', async () => {
    mockPracticeService.createReadingSession.mockResolvedValue(MOCK_READING_SESSION)
    mockPracticeService.submitReading.mockResolvedValue(MOCK_RESULT)
    const store = usePracticeStore()
    await store.startSession('reading')
    await new Promise((resolve) => setTimeout(resolve, 100))
    await store.submitSession('reading', 'sess-read-001', {})
    const calledPayload = mockPracticeService.submitReading.mock.calls[0][0]
    expect(calledPayload.duration_seconds).toBeGreaterThanOrEqual(0)
  })
})

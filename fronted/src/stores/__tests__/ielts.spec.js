/**
 * src/stores/__tests__/ielts.spec.js
 * ────────────────────────────────────
 * Unit tests for the ielts Pinia store.
 * Uses vi.hoisted() for mocks to avoid Vitest hoisting errors.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIeltsStore } from '../ielts.js'

// ── Hoisted mocks ─────────────────────────────────────────────────────────────
const { mockIeltsService, mockMapHistoryItem } = vi.hoisted(() => {
  return {
    mockIeltsService: {
      getHistory: vi.fn(),
      getProgress: vi.fn(),
      getUserStats: vi.fn(),
      getSkillRadar: vi.fn(),
      getStudyPlan: vi.fn(),
      generateStudyPlan: vi.fn(),
      extendStudyPlan: vi.fn(),
      completeStudyTask: vi.fn(),
      askDashboardCoach: vi.fn(),
    },
    // Perform real subject→skill mapping so historyBySkill getter works correctly
    mockMapHistoryItem: vi.fn((item) => ({
      ...item,
      skill: (item.skill || item.subject || 'reading').toLowerCase(),
    })),
  }
})

vi.mock('@/services/ieltsService.js', () => ({
  ieltsService: mockIeltsService,
}))

vi.mock('@/services/historyService.js', () => ({
  mapHistoryItem: mockMapHistoryItem,
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

const makePastDate = (daysAgo) => {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  return d.toISOString()
}

const MOCK_HISTORY = {
  items: [
    { id: 1, subject: 'reading', completed_at: makePastDate(0), duration_seconds: 600 },
    { id: 2, subject: 'listening', completed_at: makePastDate(1), duration_seconds: 900 },
    { id: 3, subject: 'writing', completed_at: makePastDate(0), duration_seconds: 1200 },
  ],
}

const MOCK_STATS = {
  band_scores: { Reading: '6.5', Listening: '7.0', Writing: '6.0', Speaking: '6.5' },
  streak: 5,
  days_to_exam: 30,
}

const MOCK_STUDY_PLAN = {
  days: [
    {
      day: 1,
      tasks: [
        { id: 10, title: 'Reading Practice', is_completed: false },
        { id: 11, title: 'Vocab Review', is_completed: true },
      ],
    },
  ],
  total_tasks: 2,
  completed_tasks: 1,
}

// ── Test Suite ────────────────────────────────────────────────────────────────

describe('useIeltsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // Restore real mapping on each test (clearAllMocks resets implementation)
    mockMapHistoryItem.mockImplementation((item) => ({
      ...item,
      skill: (item.skill || item.subject || 'reading').toLowerCase(),
    }))
  })

  // ── IE-01: fetchHistory — happy path ─────────────────────────────────────
  it('IE-01: fetchHistory tải và ánh xạ lịch sử làm bài thành công', async () => {
    mockIeltsService.getHistory.mockResolvedValue(MOCK_HISTORY)
    const store = useIeltsStore()
    await store.fetchHistory()
    expect(store.history).toHaveLength(3)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // ── IE-02: fetchHistory — lọc theo kỹ năng ───────────────────────────────
  it('IE-02: fetchHistory với skill truyền đúng params lên service', async () => {
    mockIeltsService.getHistory.mockResolvedValue({ items: [] })
    const store = useIeltsStore()
    await store.fetchHistory('reading')
    expect(mockIeltsService.getHistory).toHaveBeenCalledWith(
      expect.objectContaining({ subject: 'Reading' })
    )
  })

  // ── IE-03: fetchHistory — thất bại ───────────────────────────────────────
  it('IE-03: fetchHistory thất bại cập nhật error và history rỗng', async () => {
    mockIeltsService.getHistory.mockRejectedValue({ response: { data: { detail: 'Unauthorized' } } })
    const store = useIeltsStore()
    await store.fetchHistory()
    expect(store.history).toEqual([])
    expect(store.error).toBe('Unauthorized')
  })

  // ── IE-04: historyBySkill — getter ───────────────────────────────────────
  it('IE-04: historyBySkill getter lọc đúng theo kỹ năng', async () => {
    mockIeltsService.getHistory.mockResolvedValue(MOCK_HISTORY)
    const store = useIeltsStore()
    await store.fetchHistory()
    const readingHistory = store.historyBySkill('reading')
    expect(readingHistory).toHaveLength(1)
    expect(readingHistory[0].skill).toBe('reading')
  })

  // ── IE-05: historyBySkill — all ──────────────────────────────────────────
  it('IE-05: historyBySkill("all") trả về toàn bộ lịch sử', async () => {
    mockIeltsService.getHistory.mockResolvedValue(MOCK_HISTORY)
    const store = useIeltsStore()
    await store.fetchHistory()
    const all = store.historyBySkill('all')
    expect(all).toHaveLength(3)
  })

  // ── IE-06: fetchStats ─────────────────────────────────────────────────────
  it('IE-06: fetchStats tính toán bandScores, streak và daysToExam đúng', async () => {
    mockIeltsService.getUserStats.mockResolvedValue(MOCK_STATS)
    const store = useIeltsStore()
    await store.fetchStats()
    expect(store.bandScores.reading).toBe(6.5)
    expect(store.bandScores.listening).toBe(7.0)
    expect(store.bandScores.writing).toBe(6.0)
    expect(store.bandScores.speaking).toBe(6.5)
    expect(store.bandScores.overall).toBeCloseTo(6.5, 1)
    expect(store.streak).toBe(5)
    expect(store.daysToExam).toBe(30)
  })

  // ── IE-07: fetchStats — không có band scores ──────────────────────────────
  it('IE-07: fetchStats không có band scores giữ overall = 0', async () => {
    mockIeltsService.getUserStats.mockResolvedValue({ band_scores: {}, streak: 0 })
    const store = useIeltsStore()
    await store.fetchStats()
    expect(store.bandScores.overall).toBe(0)
  })

  // ── IE-08: fetchProgress ──────────────────────────────────────────────────
  it('IE-08: fetchProgress lưu kết quả vào store.progress', async () => {
    const mockProgress = [{ subject: 'reading', total_sessions: 10 }]
    mockIeltsService.getProgress.mockResolvedValue(mockProgress)
    const store = useIeltsStore()
    await store.fetchProgress()
    expect(store.progress).toEqual(mockProgress)
  })

  // ── IE-09: fetchPracticeAnalytics — activityMap ───────────────────────────
  it('IE-09: fetchPracticeAnalytics xây dựng activityMap đúng', async () => {
    mockIeltsService.getHistory.mockResolvedValue(MOCK_HISTORY)
    const store = useIeltsStore()
    await store.fetchPracticeAnalytics()
    const today = new Date().toISOString().slice(0, 10)
    // reading + writing both today → count 2
    expect(store.activityMap[today]).toBe(2)
    expect(store.weeklyStats).toHaveLength(7)
  })

  // ── IE-10: fetchSkillRadar ────────────────────────────────────────────────
  it('IE-10: fetchSkillRadar lưu dữ liệu radar kỹ năng', async () => {
    const mockRadar = { reading: 6.5, listening: 7.0, writing: 6.0, speaking: 6.0, attempts: {} }
    mockIeltsService.getSkillRadar.mockResolvedValue(mockRadar)
    const store = useIeltsStore()
    await store.fetchSkillRadar()
    expect(store.skillRadar).toEqual(mockRadar)
  })

  // ── IE-11: fetchStudyPlan ─────────────────────────────────────────────────
  it('IE-11: fetchStudyPlan tải kế hoạch học tập vào store', async () => {
    mockIeltsService.getStudyPlan.mockResolvedValue(MOCK_STUDY_PLAN)
    const store = useIeltsStore()
    await store.fetchStudyPlan()
    expect(store.studyPlanData.days).toHaveLength(1)
    expect(store.studyPlanData.total_tasks).toBe(2)
    expect(store.studyPlan.days).toHaveLength(1)
  })

  // ── IE-12: generateStudyPlan ──────────────────────────────────────────────
  it('IE-12: generateStudyPlan tạo kế hoạch mới và cập nhật store', async () => {
    const newPlan = { days: [{ day: 1, tasks: [] }], total_tasks: 0, completed_tasks: 0 }
    mockIeltsService.generateStudyPlan.mockResolvedValue(newPlan)
    const store = useIeltsStore()
    const result = await store.generateStudyPlan()
    expect(result).toBe(true)
    expect(store.studyPlanData).toEqual(newPlan)
  })

  // ── IE-13: extendStudyPlan ────────────────────────────────────────────────
  it('IE-13: extendStudyPlan mở rộng kế hoạch và cập nhật store', async () => {
    const extended = { ...MOCK_STUDY_PLAN, total_tasks: 4 }
    mockIeltsService.extendStudyPlan.mockResolvedValue(extended)
    const store = useIeltsStore()
    const result = await store.extendStudyPlan()
    expect(result).toBe(true)
    expect(store.studyPlanData.total_tasks).toBe(4)
  })

  // ── IE-14: completeStudyTask ──────────────────────────────────────────────
  it('IE-14: completeStudyTask cập nhật task in-place và tính lại completed_tasks', async () => {
    mockIeltsService.getStudyPlan.mockResolvedValue(MOCK_STUDY_PLAN)
    mockIeltsService.completeStudyTask.mockResolvedValue({ id: 10, title: 'Reading Practice', is_completed: true })
    const store = useIeltsStore()
    await store.fetchStudyPlan()
    const updated = await store.completeStudyTask(10)
    expect(updated.is_completed).toBe(true)
    const task = store.studyPlanData.days[0].tasks.find((t) => t.id === 10)
    expect(task.is_completed).toBe(true)
    // id=10 now true + id=11 already true = 2
    expect(store.studyPlanData.completed_tasks).toBe(2)
  })
})

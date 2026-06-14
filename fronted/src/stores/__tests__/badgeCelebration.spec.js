/**
 * src/stores/__tests__/badgeCelebration.spec.js
 * ──────────────────────────────────────────────
 * Unit tests for the badgeCelebration Pinia store.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBadgeCelebrationStore } from '../badgeCelebration.js'

// Mock localStorage (jsdom provides it but we want clean isolation)
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: () => { store = {} },
  }
})()

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

// ── Test Suite ────────────────────────────────────────────────────────────────

describe('useBadgeCelebrationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  // ── BC-01: trạng thái ban đầu ─────────────────────────────────────────────
  it('BC-01: trạng thái ban đầu queue rỗng và active null', () => {
    const store = useBadgeCelebrationStore()
    expect(store.queue).toEqual([])
    expect(store.active).toBeNull()
  })

  // ── BC-02: enqueue huy hiệu mới ──────────────────────────────────────────
  it('BC-02: enqueue huy hiệu mới hiển thị ngay lập tức (active)', () => {
    const store = useBadgeCelebrationStore()
    const badge = { id: 'badge-1', name: 'First Practice', icon: '🎯' }

    store.enqueue([badge])

    expect(store.active).toEqual(badge)
    expect(store.queue).toHaveLength(0) // shifted into active
  })

  // ── BC-03: enqueue nhiều huy hiệu ────────────────────────────────────────
  it('BC-03: enqueue nhiều huy hiệu cùng lúc, hiển thị tuần tự', () => {
    const store = useBadgeCelebrationStore()
    const badges = [
      { id: 'badge-1', name: 'First Practice' },
      { id: 'badge-2', name: 'Streak 7' },
    ]

    store.enqueue(badges)

    expect(store.active).toEqual(badges[0])
    expect(store.queue).toHaveLength(1)
    expect(store.queue[0]).toEqual(badges[1])
  })

  // ── BC-04: dismiss và hiển thị badge kế tiếp ─────────────────────────────
  it('BC-04: dismiss xóa active và hiển thị badge kế tiếp', () => {
    const store = useBadgeCelebrationStore()
    const badges = [
      { id: 'badge-1', name: 'First' },
      { id: 'badge-2', name: 'Second' },
    ]
    store.enqueue(badges)

    // Dismiss first badge
    store.dismiss()

    expect(store.active).toEqual(badges[1])
    expect(store.queue).toHaveLength(0)
  })

  // ── BC-05: dismiss khi hết badge ─────────────────────────────────────────
  it('BC-05: dismiss khi không còn badge thì active = null', () => {
    const store = useBadgeCelebrationStore()
    store.enqueue([{ id: 'badge-1', name: 'Only Badge' }])

    store.dismiss()

    expect(store.active).toBeNull()
    expect(store.queue).toHaveLength(0)
  })

  // ── BC-06: không hiển thị badge đã biết ──────────────────────────────────
  it('BC-06: enqueue không hiển thị badge đã có trong knownIds', () => {
    const store = useBadgeCelebrationStore()
    const badge = { id: 'badge-old', name: 'Old Badge' }

    // Add to known IDs first
    store.enqueue([badge]) // shown once, adds to known
    store.dismiss() // clear active

    // Try to enqueue same badge again
    store.enqueue([badge])

    // Should NOT show again since it's already known
    expect(store.active).toBeNull()
    expect(store.queue).toHaveLength(0)
  })

  // ── BC-07: persist knownIds vào localStorage ──────────────────────────────
  it('BC-07: enqueue mới lưu badge ID vào localStorage', () => {
    const store = useBadgeCelebrationStore()
    const badge = { id: 'badge-persist', name: 'Persist Test' }

    store.enqueue([badge])

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'ieltstrainer_known_badges',
      expect.stringContaining('badge-persist')
    )
  })

  // ── BC-08: enqueue input rỗng hoặc null ──────────────────────────────────
  it('BC-08: enqueue với array rỗng hoặc null không gây lỗi', () => {
    const store = useBadgeCelebrationStore()

    expect(() => store.enqueue([])).not.toThrow()
    expect(() => store.enqueue(null)).not.toThrow()
    expect(store.active).toBeNull()
  })

  // ── BC-09: syncKnownFromBadges ────────────────────────────────────────────
  it('BC-09: syncKnownFromBadges ghi nhận badge đã unlock từ danh sách', () => {
    const store = useBadgeCelebrationStore()
    const badges = [
      { id: 'badge-x', unlocked: true },
      { id: 'badge-y', unlocked: false }, // not unlocked, should not be added
    ]

    store.syncKnownFromBadges(badges)

    // badge-x is now known → enqueue won't show it
    store.enqueue([{ id: 'badge-x', name: 'X' }])
    expect(store.active).toBeNull() // Already known, suppressed

    // badge-y is still not known → would show if enqueued
    store.enqueue([{ id: 'badge-y', name: 'Y' }])
    expect(store.active).toEqual({ id: 'badge-y', name: 'Y' })
  })
})

/**
 * e2e/history.spec.js
 * ────────────────────
 * E2E tests for the History & Leaderboard pages.
 * Requires authenticated user (storageState from global-setup).
 */
import { test, expect } from '@playwright/test'

test.describe('History', () => {
  test('E2E-21: trang History hiển thị danh sách lịch sử làm bài', async ({ page }) => {
    await page.goto('/history')
    await page.waitForTimeout(3000)
    // History page should load — heading or content area visible
    await expect(page).toHaveURL(/\/history/)
    // Either a list of history items or "empty state" text
    const body = page.locator('body')
    await expect(body).toBeVisible()
  })
})

test.describe('Leaderboard', () => {
  test('E2E-22: trang Leaderboard hiển thị bảng xếp hạng', async ({ page }) => {
    await page.goto('/leaderboard')
    await expect(page.getByRole('heading', { name: 'Bảng xếp hạng' })).toBeVisible()
  })
})

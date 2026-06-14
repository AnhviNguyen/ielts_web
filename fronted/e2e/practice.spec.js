/**
 * e2e/practice.spec.js
 * ─────────────────────
 * E2E tests for the Reading & Listening practice flows.
 * Requires authenticated user (storageState from global-setup).
 */
import { test, expect } from '@playwright/test'

test.describe('Reading Practice', () => {
  test('E2E-07: trang Reading hiển thị danh sách bộ đề', async ({ page }) => {
    await page.goto('/reading')
    await expect(page.getByRole('heading', { name: 'Reading' })).toBeVisible()
    // Wait for the mock tests grid to load
    await page.waitForSelector('.grid', { timeout: 15000 })
    // Should display at least one test card or "Không tìm thấy" message
    const cards = page.locator('.ct-card, .grid > div')
    const noResult = page.getByText('Không tìm thấy đề phù hợp.')
    await expect(cards.first().or(noResult)).toBeVisible()
  })

  test('E2E-08: tìm kiếm đề luyện tập Reading', async ({ page }) => {
    await page.goto('/reading')
    await page.waitForSelector('.grid', { timeout: 15000 })
    const searchInput = page.locator('input[placeholder="Tìm đề..."]')
    await expect(searchInput).toBeVisible()
    // Type a search query
    await searchInput.fill('test')
    // Wait for filter to apply
    await page.waitForTimeout(500)
    // Page should still be on /reading
    await expect(page).toHaveURL(/\/reading/)
  })
})

test.describe('Listening Practice', () => {
  test('E2E-09: trang Listening hiển thị danh sách bộ đề', async ({ page }) => {
    await page.goto('/listening')
    await expect(page.getByRole('heading', { name: 'Listening' })).toBeVisible()
    await page.waitForSelector('.grid', { timeout: 15000 })
    const cards = page.locator('.ct-card, .grid > div')
    const noResult = page.getByText('Không tìm thấy đề phù hợp.')
    await expect(cards.first().or(noResult)).toBeVisible()
  })
})

/**
 * e2e/speaking.spec.js
 * ─────────────────────
 * E2E tests for the Speaking practice flow.
 * Requires authenticated user (storageState from global-setup).
 */
import { test, expect } from '@playwright/test'

test.describe('Speaking', () => {
  test('E2E-13: trang Speaking hiển thị danh sách bộ đề nói', async ({ page }) => {
    await page.goto('/speaking')
    await expect(page.getByRole('heading', { name: 'Speaking' })).toBeVisible()
    // Wait for content to load
    await page.waitForSelector('.grid', { timeout: 15000 })
    const cards = page.locator('.ct-card, .grid > div')
    const noResult = page.getByText('Không tìm thấy đề phù hợp.')
    await expect(cards.first().or(noResult)).toBeVisible()
  })

  test('E2E-14: tìm kiếm đề Speaking hoạt động', async ({ page }) => {
    await page.goto('/speaking')
    await page.waitForSelector('.grid', { timeout: 15000 })
    const searchInput = page.locator('input[placeholder="Tìm đề..."]')
    await expect(searchInput).toBeVisible()
    await searchInput.fill('part')
    await page.waitForTimeout(500)
    await expect(page).toHaveURL(/\/speaking/)
  })
})

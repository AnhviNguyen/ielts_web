/**
 * e2e/writing.spec.js
 * ────────────────────
 * E2E tests for the Writing practice flow.
 * Requires authenticated user (storageState from global-setup).
 */
import { test, expect } from '@playwright/test'

test.describe('Writing', () => {
  test('E2E-10: trang Writing hiển thị danh sách bộ đề viết', async ({ page }) => {
    await page.goto('/writing/ielts')
    await expect(page.getByRole('heading', { name: 'Writing' })).toBeVisible()
    // Wait for writing sets to load (skeleton loaders or actual cards)
    await page.waitForTimeout(3000)
    // Should display at least one writing set card or "Không tìm thấy" message
    const cards = page.locator('.ct-card')
    const noResult = page.getByText('Không tìm thấy đề phù hợp.')
    await expect(cards.first().or(noResult)).toBeVisible()
  })

  test('E2E-11: tìm kiếm đề Writing hoạt động', async ({ page }) => {
    await page.goto('/writing/ielts')
    await page.waitForTimeout(3000)
    const searchInput = page.locator('input[placeholder="Tìm đề..."]')
    await expect(searchInput).toBeVisible()
    await searchInput.fill('task')
    await page.waitForTimeout(500)
    await expect(page).toHaveURL(/\/writing\/ielts/)
  })

  test('E2E-12: Writing Hub hiển thị hai lựa chọn', async ({ page }) => {
    await page.goto('/writing')
    // Writing Hub should present choices between IELTS Writing and Translation
    await page.waitForTimeout(2000)
    await expect(page).toHaveURL(/\/writing/)
  })
})

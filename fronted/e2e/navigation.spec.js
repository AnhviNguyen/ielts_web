import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('sidebar: Reading và History', async ({ page }) => {
    const sidebar = page.locator('nav').first()
    await sidebar.getByRole('link', { name: 'Reading', exact: true }).click()
    await expect(page).toHaveURL(/\/reading/)

    await sidebar.getByRole('link', { name: 'Lịch sử' }).click()
    await expect(page).toHaveURL(/\/history/)
  })

  test('sidebar: Bảng xếp hạng', async ({ page }) => {
    await page.locator('nav').first().getByRole('link', { name: 'Bảng xếp hạng' }).click()
    await expect(page).toHaveURL(/\/leaderboard/)
    await expect(page.getByRole('heading', { name: 'Bảng xếp hạng' })).toBeVisible()
  })
})

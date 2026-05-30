import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('hiển thị header và tab điều hướng', async ({ page }) => {
    await expect(page.getByText('IELTS Academic')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Home' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Progress' })).toBeVisible()
  })

  test('chuyển tab Progress', async ({ page }) => {
    await page.getByRole('button', { name: 'Progress' }).click()
    await expect(page.getByText('Progress by Skill')).toBeVisible()
  })
})

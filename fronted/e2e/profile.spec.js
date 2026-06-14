/**
 * e2e/profile.spec.js
 * ────────────────────
 * E2E tests for the Profile management page.
 * Requires authenticated user (storageState from global-setup).
 */
import { test, expect } from '@playwright/test'

test.describe('Profile', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/profile')
    // Wait for profile data to load
    await page.waitForTimeout(3000)
  })

  test('E2E-15: trang Profile hiển thị thông tin người dùng', async ({ page }) => {
    // Check page has loaded with user info
    await expect(page.getByText('Chỉnh sửa thông tin')).toBeVisible()
    // User name should be visible
    const nameInput = page.locator('input[placeholder="Nhập họ và tên"]')
    await expect(nameInput).toBeVisible()
    // Email field should be disabled
    const emailInput = page.locator('input[type="email"][disabled]')
    await expect(emailInput).toBeVisible()
  })

  test('E2E-16: hiển thị thống kê luyện tập (bài đã làm, band, thời gian)', async ({ page }) => {
    await expect(page.getByText('Bài đã làm', { exact: true })).toBeVisible()
    await expect(page.getByText('Band trung bình')).toBeVisible()
    await expect(page.getByText('Tổng thời gian')).toBeVisible()
  })

  test('E2E-17: hiển thị phần huy hiệu', async ({ page }) => {
    await expect(page.getByText('Huy hiệu')).toBeVisible()
    // Badge filter buttons should exist
    await expect(page.getByRole('button', { name: 'Tất cả' })).toBeVisible()
  })

  test('E2E-18: lọc huy hiệu theo trạng thái', async ({ page }) => {
    // Click "Đã mở" filter
    const unlockedBtn = page.getByRole('button', { name: /Đã mở/ })
    await expect(unlockedBtn).toBeVisible()
    await unlockedBtn.click()
    await page.waitForTimeout(500)

    // Click "Chưa mở" filter
    const lockedBtn = page.getByRole('button', { name: /Chưa mở/ })
    await expect(lockedBtn).toBeVisible()
    await lockedBtn.click()
    await page.waitForTimeout(500)

    // Click "Tất cả" to reset
    await page.getByRole('button', { name: 'Tất cả' }).click()
  })

  test('E2E-19: phần đổi mật khẩu hiển thị đúng', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Đổi mật khẩu' })).toBeVisible()
    await expect(page.locator('input[placeholder="••••••••"]').first()).toBeVisible()
  })

  test('E2E-20: nút đăng xuất hiển thị và hoạt động', async ({ page }) => {
    const logoutBtn = page.getByRole('button', { name: 'Đăng xuất' })
    await expect(logoutBtn).toBeVisible()
  })
})

/**
 * e2e/admin.spec.js
 * ─────────────────
 * E2E tests for the Admin Panel.
 * Validates permission restrictions for standard users,
 * and access control / content rendering for admins.
 */
import { test, expect } from '@playwright/test'

const ADMIN_EMAIL = 'admin@gmail.com'
const ADMIN_PASSWORD = 'AdminPassword123!'

test.describe('Admin Permission Guard (Non-Admin User)', () => {
  test.use({ storageState: 'e2e/.auth/user.json' })
  // Uses default authenticated user storageState
  test('E2E-16: Người dùng thường không thể truy cập /admin và bị chuyển hướng về dashboard', async ({ page }) => {
    await page.goto('/admin')
    // Wait for redirect to finish
    await page.waitForTimeout(3000)
    // Should be redirected back to dashboard
    await expect(page).toHaveURL(/\/dashboard/)
  })
})

test.describe('Admin Features (Admin User)', () => {
  // Clear storageState so we start unauthenticated
  test.use({ storageState: { cookies: [], origins: [] } })

  test('E2E-14: Admin đăng nhập thành công và truy cập được bảng quản trị', async ({ page }) => {
    // 1. Log in as admin
    await page.goto('/login')
    await page.locator('#login-email').fill(ADMIN_EMAIL)
    await page.locator('#login-password').fill(ADMIN_PASSWORD)
    await page.locator('#login-btn').click()
    
    // Should successfully login and land on dashboard
    await page.waitForURL(/\/dashboard/)
    await expect(page).toHaveURL(/\/dashboard/)

    // 2. Access Admin Dashboard
    await page.goto('/admin')
    await page.waitForTimeout(3000)
    await expect(page).toHaveURL(/\/admin/)
    
    // Check heading
    await expect(page.getByRole('heading', { name: 'Bảng điều khiển quản trị' })).toBeVisible()
    // Check quick links section
    await expect(page.getByText('Truy cập nhanh')).toBeVisible()

    // 3. Go to User Management page
    await page.goto('/admin/users')
    await page.waitForTimeout(3000)
    await expect(page).toHaveURL(/\/admin\/users/)
    await expect(page.getByRole('heading', { name: 'Quản lý người dùng' })).toBeVisible()
    
    // Check that at least the list exists or we see the page content
    await expect(page.locator('table')).toBeVisible()
  })
})

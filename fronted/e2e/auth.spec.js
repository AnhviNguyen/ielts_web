import { test, expect } from '@playwright/test'
import { E2E_EMAIL, E2E_PASSWORD, loginViaUi } from './helpers/auth.js'

test.describe('Auth', () => {
  test('trang đăng nhập hiển thị form', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: 'Chào mừng trở lại!' })).toBeVisible()
    await expect(page.locator('#login-email')).toBeVisible()
    await expect(page.locator('#login-password')).toBeVisible()
    await expect(page.locator('#login-btn')).toBeVisible()
  })

  test('chưa đăng nhập thì /dashboard chuyển về /login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })

  test('đăng nhập sai mật khẩu hiển thị lỗi', async ({ page }) => {
    await page.goto('/login')
    await page.locator('#login-email').fill(E2E_EMAIL)
    await page.locator('#login-password').fill('wrong-password-xyz')
    await page.locator('#login-btn').click()
    await expect(page.locator('.error-msg')).toBeVisible()
    await expect(page).toHaveURL(/\/login/)
  })

  test('đăng nhập thành công vào dashboard', async ({ page }) => {
    await loginViaUi(page)
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('đã đăng nhập thì /login chuyển về dashboard', async ({ page }) => {
    await loginViaUi(page)
    await page.goto('/login')
    await expect(page).toHaveURL(/\/dashboard/)
  })
})

export const E2E_EMAIL = process.env.E2E_USER_EMAIL || 'e2e@example.com'
export const E2E_PASSWORD = process.env.E2E_USER_PASSWORD || 'TestPassword123!'

/** Log in via UI and wait for dashboard. */
export async function loginViaUi(page, email = E2E_EMAIL, password = E2E_PASSWORD) {
  await page.goto('/login')
  await page.locator('#login-email').fill(email)
  await page.locator('#login-password').fill(password)
  await page.locator('#login-btn').click()
  await page.waitForURL(/\/dashboard/)
}

/**
 * e2e/placement.spec.js
 * ─────────────────────
 * E2E tests for the Placement Onboarding Flow.
 * Evaluates registering a new user and completing the placement onboarding.
 */
import { test, expect } from '@playwright/test'

test.describe('Placement Onboarding Flow', () => {
  test('E2E-05 & E2E-06: Đăng ký người dùng mới -> Hiện Placement Gate -> Nhập điểm thủ công -> Vào Dashboard', async ({ page }) => {
    const randomSuffix = Math.floor(Math.random() * 100000)
    const email = `e2e_placement_${randomSuffix}@example.com`
    const password = 'TestPassword123!'
    const fullName = 'E2E Onboarding User'

    // 1. Go to register page
    await page.goto('/register')
    await expect(page.locator('#reg-name')).toBeVisible()

    // 2. Fill registration form
    await page.locator('#reg-name').fill(fullName)
    await page.locator('#reg-email').fill(email)
    await page.locator('#reg-password').fill(password)
    
    // Select a target band
    await page.locator('select.form-input').selectOption({ label: '7.5' })

    // 3. Submit registration
    await page.locator('#register-btn').click()

    // 4. Wait for redirection
    // Since REQUIRE_EMAIL_VERIFICATION might be false, or if it is true we might need to handle verify-email.
    // Let's check which page we end up on. If we end up on /verify-email, we will use a backend bypass or a known code if possible.
    // However, if REQUIRE_EMAIL_VERIFICATION is false, we should go directly to dashboard.
    // Let's assert we either get redirected to dashboard or verification.
    await page.waitForURL(/.*(verify-email|dashboard)/, { timeout: 15000 })
    
    if (page.url().includes('verify-email')) {
      // If we are at verify-email, we will skip the remainder of the E2E verification test or verify with 123456 (if mocked/configured).
      // But we plan to disable require email verification for E2E. Let's make sure it handles both.
      test.skip(true, 'Skip verify-email verification inside onboarding since OTP requires backend log extraction.')
      return
    }

    // 5. User is on Dashboard and needs placement. The PlacementGate modal should be visible.
    await expect(page.locator('.choice-card').first()).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('Set your starting point')).toBeVisible()

    // 6. Click "Enter existing scores" (the second choice card)
    await page.getByText('Enter existing scores').click()

    // 7. Verify the inputs for manual entry are visible
    await expect(page.getByText('Reading')).toBeVisible()
    await expect(page.getByText('Listening')).toBeVisible()

    // Fill in manual bands
    await page.locator('label:has-text("Reading") input').fill('6.5')
    await page.locator('label:has-text("Listening") input').fill('7.0')
    await page.locator('label:has-text("Writing") input').fill('6.0')
    await page.locator('label:has-text("Speaking") input').fill('6.5')

    // 8. Submit manual scores
    await page.locator('button[type="submit"]:has-text("Save starting bands")').click()

    // 9. Modal should close and we are on dashboard with no placement modal visible
    await expect(page.locator('.choice-card')).not.toBeVisible({ timeout: 15000 })
    
    // Check if Dashboard heading is visible on the dashboard now
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
  })
})

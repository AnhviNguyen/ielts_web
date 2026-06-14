/**
 * e2e/vocabulary.spec.js
 * ───────────────────────
 * E2E tests for the Vocabulary module.
 * Requires authenticated user (storageState from global-setup).
 */
import { test, expect } from '@playwright/test'

test.describe('Vocabulary', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/vocabulary')
    // Wait for vocabulary page to initialize
    await page.waitForTimeout(3000)
  })

  test('E2E-17 & E2E-18: Quản lý từ vựng -> Tạo topic mới -> Thêm từ mới vào topic', async ({ page }) => {
    // 1. Verify vocabulary hub loaded
    await expect(page.getByText('Từ vựng của tôi')).toBeVisible()

    // 2. Open Add Topic modal
    const addTopicBtn = page.locator('.sidebar-add-btn')
    await expect(addTopicBtn).toBeVisible()
    await addTopicBtn.click()

    // 3. Fill topic name and save
    const topicNameInput = page.locator('.topic-input')
    await expect(topicNameInput).toBeVisible()
    
    const randomSuffix = Math.floor(Math.random() * 1000)
    const testTopicName = `E2E Topic ${randomSuffix}`
    await topicNameInput.fill(testTopicName)
    
    // Save
    await page.locator('.modal-sm-footer .btn-green').click()
    await page.waitForTimeout(1000)

    // 4. Verify topic is created and visible in the sidebar list
    const topicItem = page.getByText(testTopicName)
    await expect(topicItem).toBeVisible()

    // 5. Select the created topic
    await topicItem.click()
    await page.waitForTimeout(1000)

    // 6. Switch to "Quản lý từ" (Word management) tab
    const manageTabBtn = page.locator('button.view-tab:has-text("Quản lý từ")')
    await expect(manageTabBtn).toBeVisible()
    await manageTabBtn.click()
    await page.waitForTimeout(1000)

    // 7. Click "Thêm từ" (Add word) button
    const addWordBtn = page.locator('button.add-word-btn').first()
    await expect(addWordBtn).toBeVisible()
    await addWordBtn.click()

    // 8. Fill word info in the modal
    const wordInput = page.locator('input[placeholder="e.g. perseverance"]')
    const meaningViInput = page.locator('input[placeholder="sự kiên trì, bền bỉ"]')
    await expect(wordInput).toBeVisible()

    await wordInput.fill('Alacrity')
    await meaningViInput.fill('sự sốt sắng, hoạt bát')

    // Click Save
    await page.locator('.modal-lg .btn-green').click()
    await page.waitForTimeout(1000)

    // 9. Verify the word appears in the list
    await expect(page.getByText('Alacrity')).toBeVisible()
    await expect(page.getByText('sự sốt sắng, hoạt bát')).toBeVisible()
  })
})

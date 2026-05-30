/**
 * Ensures E2E test user exists and saves authenticated browser state.
 * Requires backend at E2E_API_URL (default http://localhost:8000).
 */

import fs from 'node:fs'
import path from 'node:path'
import { chromium } from '@playwright/test'

const API_URL = process.env.E2E_API_URL || 'http://localhost:8000'
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173'
const EMAIL = process.env.E2E_USER_EMAIL || 'e2e@example.com'
const PASSWORD = process.env.E2E_USER_PASSWORD || 'TestPassword123!'
const AUTH_FILE = path.join('e2e', '.auth', 'user.json')

async function api(pathname, options = {}) {
  const res = await fetch(`${API_URL}${pathname}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const text = await res.text()
  let body = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = text
  }
  return { ok: res.ok, status: res.status, body }
}

export default async function globalSetup() {
  const health = await api('/health')
  if (!health.ok) {
    throw new Error(
      `Backend không phản hồi tại ${API_URL}/health — hãy chạy API trước (port 8000).`
    )
  }

  const login = await api('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
  })

  if (!login.ok) {
    const register = await api('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: EMAIL,
        password: PASSWORD,
        full_name: 'E2E Test User',
      }),
    })

    if (!register.ok && register.status !== 409) {
      const detail = register.body?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
        : detail || JSON.stringify(register.body)
      throw new Error(`Không tạo được user E2E (${EMAIL}): ${msg}`)
    }
  }

  fs.mkdirSync(path.dirname(AUTH_FILE), { recursive: true })
  const browser = await chromium.launch()
  const context = await browser.newContext()
  const page = await context.newPage()
  await page.goto(`${BASE_URL}/login`)
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.locator('#login-btn').click()
  await page.waitForURL(/\/dashboard/)
  await context.storageState({ path: AUTH_FILE })
  await browser.close()
}

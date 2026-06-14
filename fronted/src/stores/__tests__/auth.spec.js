/**
 * src/stores/__tests__/auth.spec.js
 * ───────────────────────────────────
 * Unit tests for the auth Pinia store.
 *
 * Strategy: mock `authService` and `tokenStore` so no real HTTP calls are made.
 * Each test creates a fresh Pinia instance via createPinia() for isolation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth.js'

// ── Hoisted mocks (must come before vi.mock calls) ────────────────────────────
const { mockAuthService, mockGetAccessToken, mockSetTokens, mockClearTokens } = vi.hoisted(() => {
  const svc = {
    register: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
    googleAuth: vi.fn(),
    login: vi.fn(),
    refresh: vi.fn(),
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    uploadAvatar: vi.fn(),
    activityPing: vi.fn(),
    changePassword: vi.fn(),
    logout: vi.fn(),
  }
  return {
    mockAuthService: svc,
    mockGetAccessToken: vi.fn(() => null),
    mockSetTokens: vi.fn(),
    mockClearTokens: vi.fn(),
  }
})

// ── Module-level mocks ────────────────────────────────────────────────────────

vi.mock('@/api/tokenStore.js', () => ({
  getAccessToken: mockGetAccessToken,
  setTokens: mockSetTokens,
  clearTokens: mockClearTokens,
}))

vi.mock('@/router/index.js', () => ({
  default: {
    currentRoute: { value: { path: '/dashboard' } },
    push: vi.fn().mockResolvedValue(undefined),
  },
}))

vi.mock('@/stores/fullExam.js', () => ({
  useFullExamStore: vi.fn(() => ({ clear: vi.fn() })),
}))

vi.mock('@/services/authService.js', () => ({
  authService: mockAuthService,
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

const MOCK_PROFILE = { id: 1, email: 'user@test.com', full_name: 'Test User', role: 'student', streak: 5 }
const MOCK_TOKEN = 'mock.jwt.token'

function makeAxiosError(status, detail) {
  return { response: { status, data: { detail } } }
}

// ── Test Suite ────────────────────────────────────────────────────────────────

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockGetAccessToken.mockReturnValue(null)
  })

  // ── FE-01: Initial state ──────────────────────────────────────────────────
  it('FE-01: trạng thái mặc định ban đầu đúng', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.isAdmin).toBe(false)
    expect(store.profile).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // ── FE-02: isAdmin getter ─────────────────────────────────────────────────
  it('FE-02: isAdmin trả về true khi role=admin', async () => {
    mockAuthService.login.mockResolvedValue({ access_token: MOCK_TOKEN })
    mockAuthService.getProfile.mockResolvedValue({ ...MOCK_PROFILE, role: 'admin' })
    const store = useAuthStore()
    await store.login('admin@test.com', 'Password1!')
    expect(store.isAdmin).toBe(true)
  })

  // ── FE-03: register — happy path ──────────────────────────────────────────
  it('FE-03: register thành công trả về { needsVerification: true }', async () => {
    mockAuthService.register.mockResolvedValue({ needs_verification: true, email: 'new@test.com' })
    const store = useAuthStore()
    const result = await store.register('new@test.com', 'Password1!', 'New User')
    expect(result).toEqual({ needsVerification: true, email: 'new@test.com' })
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // ── FE-04: register — trùng email ────────────────────────────────────────
  it('FE-04: register với email trùng cập nhật error và trả về false', async () => {
    mockAuthService.register.mockRejectedValue(makeAxiosError(409, 'Email already registered'))
    const store = useAuthStore()
    const result = await store.register('dup@test.com', 'Password1!', 'Dup')
    expect(result).toBe(false)
    expect(store.error).toBe('Email already registered')
  })

  // ── FE-05: login — thành công ────────────────────────────────────────────
  it('FE-05: login thành công lưu token và fetch profile', async () => {
    mockAuthService.login.mockResolvedValue({ access_token: MOCK_TOKEN })
    mockAuthService.getProfile.mockResolvedValue(MOCK_PROFILE)
    const store = useAuthStore()
    const result = await store.login('user@test.com', 'Password1!')
    expect(result).toBe(true)
    expect(store.isAuthenticated).toBe(true)
    expect(store.profile).toEqual(MOCK_PROFILE)
    expect(store.userName).toBe('Test User')
  })

  // ── FE-06: login — sai mật khẩu ──────────────────────────────────────────
  it('FE-06: login sai mật khẩu trả về false và cập nhật error', async () => {
    mockAuthService.login.mockRejectedValue(makeAxiosError(401, 'Incorrect credentials'))
    const store = useAuthStore()
    const result = await store.login('user@test.com', 'WrongPass!')
    expect(result).toBe(false)
    expect(store.error).toBeTruthy()
    expect(store.isAuthenticated).toBe(false)
  })

  // ── FE-07: login — chưa xác minh OTP ─────────────────────────────────────
  it('FE-07: login tài khoản chưa xác minh OTP trả về "not_verified"', async () => {
    mockAuthService.login.mockRejectedValue(makeAxiosError(403, 'email_not_verified'))
    const store = useAuthStore()
    const result = await store.login('unverified@test.com', 'Password1!')
    expect(result).toBe('not_verified')
  })

  // ── FE-08: verifyEmail ────────────────────────────────────────────────────
  it('FE-08: verifyEmail thành công lưu token và fetch profile', async () => {
    mockAuthService.verifyEmail.mockResolvedValue({ access_token: MOCK_TOKEN })
    mockAuthService.getProfile.mockResolvedValue(MOCK_PROFILE)
    const store = useAuthStore()
    const result = await store.verifyEmail('user@test.com', '123456')
    expect(result).toBe(true)
    expect(store.isAuthenticated).toBe(true)
  })

  // ── FE-09: verifyEmail — sai OTP ─────────────────────────────────────────
  it('FE-09: verifyEmail sai OTP trả về false và cập nhật error', async () => {
    mockAuthService.verifyEmail.mockRejectedValue(makeAxiosError(400, 'Invalid OTP'))
    const store = useAuthStore()
    const result = await store.verifyEmail('user@test.com', 'wrong')
    expect(result).toBe(false)
    expect(store.error).toBeTruthy()
  })

  // ── FE-10: logout ─────────────────────────────────────────────────────────
  it('FE-10: logout xóa session local và gọi authService.logout', async () => {
    mockAuthService.login.mockResolvedValue({ access_token: MOCK_TOKEN })
    mockAuthService.getProfile.mockResolvedValue(MOCK_PROFILE)
    mockAuthService.logout.mockResolvedValue({})
    const store = useAuthStore()
    await store.login('user@test.com', 'Password1!')
    expect(store.isAuthenticated).toBe(true)
    await store.logout()
    expect(store.profile).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(mockAuthService.logout).toHaveBeenCalledTimes(1)
  })

  // ── FE-11: refreshSession — token hiện có, profile thiếu ─────────────────
  it('FE-11: refreshSession fetch lại profile nếu token tồn tại nhưng profile null', async () => {
    mockAuthService.getProfile.mockResolvedValue(MOCK_PROFILE)
    const store = useAuthStore()
    store.token = MOCK_TOKEN
    store.profile = null
    const result = await store.refreshSession()
    expect(result).toBe(true)
    expect(store.profile).toEqual(MOCK_PROFILE)
  })

  // ── FE-12: refreshSession — no token, refresh cookie thành công ───────────
  it('FE-12: refreshSession không có token thì gọi authService.refresh', async () => {
    mockAuthService.refresh.mockResolvedValue({ access_token: MOCK_TOKEN })
    mockAuthService.getProfile.mockResolvedValue(MOCK_PROFILE)
    const store = useAuthStore()
    store.token = null
    const result = await store.refreshSession()
    expect(result).toBe(true)
    expect(mockAuthService.refresh).toHaveBeenCalledTimes(1)
  })

  // ── FE-13: refreshSession — refresh thất bại ─────────────────────────────
  it('FE-13: refreshSession thất bại xóa auth và trả về false', async () => {
    mockAuthService.refresh.mockRejectedValue(makeAxiosError(401, 'Refresh token expired'))
    const store = useAuthStore()
    store.token = null
    const result = await store.refreshSession()
    expect(result).toBe(false)
    expect(store.isAuthenticated).toBe(false)
  })

  // ── FE-14: updateProfile ──────────────────────────────────────────────────
  it('FE-14: updateProfile cập nhật profile.value trong store', async () => {
    const updatedProfile = { ...MOCK_PROFILE, full_name: 'Updated Name' }
    mockAuthService.updateProfile.mockResolvedValue(updatedProfile)
    const store = useAuthStore()
    await store.updateProfile({ full_name: 'Updated Name' })
    expect(store.profile).toEqual(updatedProfile)
  })

  // ── FE-15: changePassword ─────────────────────────────────────────────────
  it('FE-15: changePassword thành công trả về true', async () => {
    mockAuthService.changePassword.mockResolvedValue({})
    const store = useAuthStore()
    const result = await store.changePassword('OldPass1!', 'NewPass1!')
    expect(result).toBe(true)
    expect(store.error).toBeNull()
  })

  // ── FE-16: changePassword — sai mật khẩu hiện tại ───────────────────────
  it('FE-16: changePassword sai mật khẩu hiện tại trả về false và cập nhật error', async () => {
    mockAuthService.changePassword.mockRejectedValue(makeAxiosError(401, 'Wrong current password'))
    const store = useAuthStore()
    const result = await store.changePassword('WrongOld', 'NewPass1!')
    expect(result).toBe(false)
    expect(store.error).toBeTruthy()
  })

  // ── FE-17: activityPing — cập nhật streak ────────────────────────────────
  it('FE-17: activityPing cập nhật streak trong profile', async () => {
    mockAuthService.login.mockResolvedValue({ access_token: MOCK_TOKEN })
    mockAuthService.getProfile.mockResolvedValue(MOCK_PROFILE)
    mockAuthService.activityPing.mockResolvedValue({ streak: 6, message: 'Streak updated' })
    const store = useAuthStore()
    await store.login('user@test.com', 'Password1!')
    await store.activityPing()
    expect(store.profile.streak).toBe(6)
  })

  // ── FE-18: uploadAvatar ───────────────────────────────────────────────────
  it('FE-18: uploadAvatar thành công gọi fetchProfile để refresh dữ liệu', async () => {
    mockAuthService.uploadAvatar.mockResolvedValue({})
    mockAuthService.getProfile.mockResolvedValue({ ...MOCK_PROFILE, avatar_url: 'https://s3.example/avatar.jpg' })
    const store = useAuthStore()
    const mockFile = new File(['content'], 'avatar.jpg', { type: 'image/jpeg' })
    const result = await store.uploadAvatar(mockFile)
    expect(result).toBe(true)
    expect(mockAuthService.uploadAvatar).toHaveBeenCalledWith(mockFile)
    expect(mockAuthService.getProfile).toHaveBeenCalledTimes(1)
  })
})

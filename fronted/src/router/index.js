/**
 * src/router/index.js
 * ────────────────────
 * LinguaIELTS route configuration with auth guards.
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const routes = [
  { path: '/', redirect: '/dashboard' },

  // Public routes
  { path: '/login',    component: () => import('@/views/auth/Login.vue'),    meta: { public: true } },
  { path: '/register', component: () => import('@/views/auth/Register.vue'), meta: { public: true } },
  { path: '/verify-email', component: () => import('@/views/auth/VerifyEmail.vue'), meta: { public: true } },
  { path: '/auth/google/callback', component: () => import('@/views/auth/GoogleCallback.vue'), meta: { public: true, skipRefresh: true } },
  { path: '/forgot-password', component: () => import('@/views/auth/ForgotPassword.vue'), meta: { public: true } },
  { path: '/reset-password', component: () => import('@/views/auth/ResetPassword.vue'), meta: { public: true } },

  // Protected routes
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true },
    // ?tab= query param handled inside Dashboard.vue — no children needed
  },
  { path: '/admin', component: () => import('@/views/admin/AdminDashboard.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users', component: () => import('@/views/admin/AdminUsers.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users/:id', component: () => import('@/views/admin/AdminUserDetail.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/leaderboard', component: () => import('@/views/admin/AdminLeaderboard.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/system-vocab', component: () => import('@/views/admin/AdminSystemVocab.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/content/writing', component: () => import('@/views/admin/AdminWritingContent.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/content/mock-tests', component: () => import('@/views/admin/AdminMockContent.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/reading',    component: () => import('@/views/Reading.vue'),     meta: { requiresAuth: true } },
  { path: '/listening',  component: () => import('@/views/Listening.vue'),   meta: { requiresAuth: true } },

  // Writing hub — choose between Translation Practice and IELTS Writing
  { path: '/writing',               component: () => import('@/views/writing/WritingHub.vue'),          meta: { requiresAuth: true } },
  { path: '/writing/ielts',         component: () => import('@/views/Writing.vue'),                     meta: { requiresAuth: true } },
  { path: '/writing/translation',   component: () => import('@/views/writing/TranslationHub.vue'),      meta: { requiresAuth: true } },
  { path: '/writing/translation/practice/:topicId', component: () => import('@/views/writing/TranslationPractice.vue'), meta: { requiresAuth: true } },
  { path: '/writing/translation/:stepId', component: () => import('@/views/writing/TranslationStep.vue'), meta: { requiresAuth: true } },
  { path: '/speaking',   component: () => import('@/views/Speaking.vue'),    meta: { requiresAuth: true } },
  { path: '/vocabulary', component: () => import('@/views/Vocabulary.vue'),  meta: { requiresAuth: true } },
  {
    path: '/shadowing',
    name: 'Shadowing',
    component: () => import('@/views/Shadowing.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/shadowing/:videoId',
    name: 'ShadowingPractice',
    component: () => import('@/views/Shadowing.vue'),
    meta: { requiresAuth: true, studio: true },
  },
  {
    path: '/vocabulary/practice/:topicId',
    name: 'VocabPractice',
    component: () => import('@/views/VocabPractice.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/history',    component: () => import('@/views/History.vue'),     meta: { requiresAuth: true } },
  { path: '/profile',      component: () => import('@/views/Profile.vue'),      meta: { requiresAuth: true } },
  { path: '/leaderboard', component: () => import('@/views/Leaderboard.vue'), meta: { requiresAuth: false } },
  { path: '/guide', name: 'Guide', component: () => import('@/views/Guide.vue'), meta: { requiresAuth: true } },
  { path: '/full-exam', component: () => import('@/views/full-exam/FullExamHub.vue'), meta: { requiresAuth: true } },
  { path: '/full-exam/break', component: () => import('@/views/full-exam/FullExamBreak.vue'), meta: { requiresAuth: true, studio: true } },
  { path: '/full-exam/writing', component: () => import('@/views/full-exam/FullExamWriting.vue'), meta: { requiresAuth: true, studio: true } },
  { path: '/full-exam/result', component: () => import('@/views/full-exam/FullExamResult.vue'), meta: { requiresAuth: true } },
  { path: '/results/:sessionId', component: () => import('@/views/Result.vue'), meta: { requiresAuth: true } },

  { path: '/writing/editor/:topicId', component: () => import('@/views/WritingEditor.vue'), meta: { requiresAuth: true } },
  { path: '/speaking/result', name: 'SpeakingResult', component: () => import('@/views/SpeakingResult.vue'), meta: { requiresAuth: true } },
  { path: '/mock-tests/:id', component: () => import('@/views/mock-tests/MockTestMode.vue'), meta: { requiresAuth: true } },
  { path: '/quiz/:quizId', component: () => import('@/views/mock-tests/QuizRunner.vue'), meta: { requiresAuth: true } },
  { path: '/quiz/:quizId/result', component: () => import('@/views/mock-tests/QuizResult.vue'), meta: { requiresAuth: true } },
  {
    path: '/review/:sessionId',
    name: 'ReviewAnswer',
    component: () => import('@/views/ReviewAnswer.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/review/quiz/:quizId',
    name: 'ReviewAnswerByQuiz',
    component: () => import('@/views/ReviewAnswer.vue'),
    meta: { requiresAuth: true },
  },

  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// Navigation guard
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // OAuth callback: always pass through — it manages its own auth state
  if (to.meta.skipRefresh) return true

  const authenticated = auth.isAuthenticated || await auth.refreshSession()
  if (to.meta.requiresAuth && !authenticated) return '/login'
  if (to.meta.public && authenticated) return '/dashboard'
  if (to.meta.requiresAdmin) {
    await auth.fetchProfile()
    if (!auth.isAdmin) return '/dashboard'
  }
  return true
})

export default router

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

  // Protected routes
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true },
    // ?tab= query param handled inside Dashboard.vue — no children needed
  },
  { path: '/reading',    component: () => import('@/views/Reading.vue'),     meta: { requiresAuth: true } },
  { path: '/listening',  component: () => import('@/views/Listening.vue'),   meta: { requiresAuth: true } },
  { path: '/writing',    component: () => import('@/views/Writing.vue'),     meta: { requiresAuth: true } },
  { path: '/speaking',   component: () => import('@/views/Speaking.vue'),    meta: { requiresAuth: true } },
  { path: '/vocabulary', component: () => import('@/views/Vocabulary.vue'),  meta: { requiresAuth: true } },
  { path: '/history',    component: () => import('@/views/History.vue'),     meta: { requiresAuth: true } },
  { path: '/profile',      component: () => import('@/views/Profile.vue'),      meta: { requiresAuth: true } },
  { path: '/leaderboard', component: () => import('@/views/Leaderboard.vue'), meta: { requiresAuth: false } },
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
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return '/login'
  if (to.meta.public && auth.isAuthenticated) return '/dashboard'
  return true
})

export default router

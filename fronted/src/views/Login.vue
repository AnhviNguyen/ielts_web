<!-- src/views/Login.vue -->
<template>
  <div class="auth-page">
    <div class="auth-bg">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
    </div>

    <div class="auth-card card">
      <div class="auth-header">
        <div class="auth-logo">⚡</div>
        <h1>Welcome back</h1>
        <p class="text-muted">Sign in to continue your learning journey</p>
      </div>

      <Transition name="fade">
        <div v-if="authStore.error" class="alert alert-error mb-md">
          {{ authStore.error }}
        </div>
      </Transition>

      <form @submit.prevent="handleLogin" id="login-form">
        <div class="form-group">
          <label class="form-label" for="login-email">Email address</label>
          <input
            id="login-email"
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="login-password">Password</label>
          <div class="input-with-icon">
            <input
              id="login-password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              placeholder="Your password"
              required
              autocomplete="current-password"
            />
            <button type="button" class="eye-btn" @click="showPassword = !showPassword">
              {{ showPassword ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>

        <button
          id="login-submit"
          type="submit"
          class="btn btn-primary btn-full btn-lg mt-md"
          :disabled="authStore.loading"
        >
          <span v-if="authStore.loading" class="spinner"></span>
          <span v-else>Sign In</span>
        </button>
      </form>

      <div class="auth-footer">
        <p class="text-muted">
          Don't have an account?
          <RouterLink to="/register" class="link-primary">Create one</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const authStore   = useAuthStore()
const router      = useRouter()
const showPassword = ref(false)
const form = reactive({ email: '', password: '' })

async function handleLogin() {
  authStore.error = null
  const ok = await authStore.login(form.email, form.password)
  if (ok) router.push('/dashboard')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  padding: 2rem 1rem;
  position: relative; overflow: hidden;
}
.auth-bg { position: absolute; inset: 0; z-index: 0; }
.bg-orb {
  position: absolute; border-radius: 50%;
  filter: blur(80px); opacity: 0.15;
}
.orb-1 { width: 500px; height: 500px; background: var(--color-primary); top: -100px; left: -100px; }
.orb-2 { width: 400px; height: 400px; background: var(--color-secondary); bottom: -80px; right: -80px; }

.auth-card {
  position: relative; z-index: 1;
  width: 100%; max-width: 420px;
  padding: 2.5rem;
}
.auth-header { text-align: center; margin-bottom: 2rem; }
.auth-logo { font-size: 2.5rem; margin-bottom: 0.75rem; }
.auth-header h1 { margin-bottom: 0.5rem; }

.input-with-icon { position: relative; }
.input-with-icon .form-input { padding-right: 3rem; }
.eye-btn {
  position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; font-size: 1rem; padding: 0;
}

.auth-footer { margin-top: 1.5rem; text-align: center; }
.link-primary { color: var(--color-primary); font-weight: 600; }
.link-primary:hover { color: var(--color-primary-h); }
</style>

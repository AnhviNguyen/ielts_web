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

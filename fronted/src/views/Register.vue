<!-- src/views/Register.vue -->
<template>
  <div class="auth-page">
    <div class="auth-bg">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
    </div>

    <div class="auth-card card">
      <div class="auth-header">
        <div class="auth-logo">⚡</div>
        <h1>Create account</h1>
        <p class="text-muted">Start your learning journey today</p>
      </div>

      <Transition name="fade">
        <div v-if="authStore.error" class="alert alert-error mb-md">{{ authStore.error }}</div>
      </Transition>
      <Transition name="fade">
        <div v-if="localError" class="alert alert-error mb-md">{{ localError }}</div>
      </Transition>

      <form @submit.prevent="handleRegister" id="register-form">
        <div class="form-group">
          <label class="form-label" for="reg-name">Full name</label>
          <input id="reg-name" v-model="form.fullName" type="text" class="form-input"
            placeholder="John Doe" autocomplete="name" />
        </div>
        <div class="form-group">
          <label class="form-label" for="reg-email">Email address</label>
          <input id="reg-email" v-model="form.email" type="email" class="form-input"
            placeholder="you@example.com" required autocomplete="email" />
        </div>
        <div class="form-group">
          <label class="form-label" for="reg-password">Password</label>
          <input id="reg-password" v-model="form.password" type="password" class="form-input"
            placeholder="At least 6 characters" required autocomplete="new-password" />
          <div class="password-strength" v-if="form.password">
            <div class="strength-bar">
              <div class="strength-fill" :style="{ width: strengthPct + '%', background: strengthColor }"></div>
            </div>
            <span class="strength-label" :style="{ color: strengthColor }">{{ strengthLabel }}</span>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label" for="reg-confirm">Confirm password</label>
          <input id="reg-confirm" v-model="form.confirm" type="password" class="form-input"
            placeholder="Repeat password" required autocomplete="new-password" />
        </div>

        <button id="register-submit" type="submit" class="btn btn-primary btn-full btn-lg mt-md"
          :disabled="authStore.loading">
          <span v-if="authStore.loading" class="spinner"></span>
          <span v-else>Create Account</span>
        </button>
      </form>

      <div class="auth-footer">
        <p class="text-muted">
          Already have an account?
          <RouterLink to="/login" class="link-primary">Sign in</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const authStore = useAuthStore()
const router    = useRouter()
const localError = ref('')
const form = reactive({ fullName: '', email: '', password: '', confirm: '' })

const strengthPct = computed(() => {
  const p = form.password
  if (!p) return 0
  let s = 0
  if (p.length >= 6)  s += 25
  if (p.length >= 10) s += 25
  if (/[A-Z]/.test(p)) s += 25
  if (/[0-9!@#$%^&*]/.test(p)) s += 25
  return s
})
const strengthColor = computed(() => {
  if (strengthPct.value <= 25) return '#f64c72'
  if (strengthPct.value <= 50) return '#f7b731'
  if (strengthPct.value <= 75) return '#4ecdc4'
  return '#43e97b'
})
const strengthLabel = computed(() => {
  if (strengthPct.value <= 25) return 'Weak'
  if (strengthPct.value <= 50) return 'Fair'
  if (strengthPct.value <= 75) return 'Good'
  return 'Strong'
})

async function handleRegister() {
  localError.value   = ''
  authStore.error    = null
  if (form.password !== form.confirm) {
    localError.value = 'Passwords do not match'
    return
  }
  const ok = await authStore.register(form.email, form.password, form.fullName)
  if (ok) router.push('/dashboard')
}
</script>

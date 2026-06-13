<template>
  <div class="auth-page auth-page--centered">
    <AuthThemeToggle />
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-mark font-display">Lingua<span>IELTS</span></div>
      </div>
      <h1 class="auth-title font-display">Đặt lại mật khẩu</h1>

      <form v-if="token" @submit.prevent="submit">
        <div class="form-group">
          <label class="form-label">Mật khẩu mới</label>
          <input v-model="password" type="password" class="form-input" minlength="6" required />
        </div>
        <div class="form-group">
          <label class="form-label">Xác nhận</label>
          <input v-model="confirm" type="password" class="form-input" required />
        </div>
        <div v-if="error" class="error-msg">{{ error }}</div>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Đang lưu...' : 'Đặt lại mật khẩu' }}
        </button>
      </form>

      <div v-else class="error-msg">Liên kết không hợp lệ. Yêu cầu email mới.</div>

      <div class="auth-footer mt-4">
        <router-link to="/login" class="auth-link">Đăng nhập</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authService } from '@/services/authService.js'
import AuthThemeToggle from '@/components/auth/AuthThemeToggle.vue'

const route = useRoute()
const router = useRouter()
const token = computed(() => route.query.token || '')
const password = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  if (password.value !== confirm.value) {
    error.value = 'Mật khẩu xác nhận không khớp'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await authService.resetPassword(token.value, password.value)
    router.push('/login')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Đặt lại thất bại'
  } finally {
    loading.value = false
  }
}
</script>

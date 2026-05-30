<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-mark font-display">Lingua<span>IELTS</span></div>
      </div>
      <h1 class="auth-title font-display">Quên mật khẩu</h1>
      <p class="auth-sub">Nhập email đăng ký — chúng tôi gửi liên kết đặt lại mật khẩu.</p>

      <form v-if="!sent" @submit.prevent="submit">
        <div class="form-group">
          <label class="form-label" for="fp-email">Email</label>
          <input id="fp-email" v-model="email" type="email" class="form-input" required />
        </div>
        <div v-if="error" class="error-msg">{{ error }}</div>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Đang gửi...' : 'Gửi liên kết' }}
        </button>
      </form>

      <div v-else class="success-msg">{{ message }}</div>

      <div class="auth-footer mt-4">
        <router-link to="/login" class="auth-link">← Quay lại đăng nhập</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authService } from '@/services/authService.js'

const email = ref('')
const loading = ref(false)
const error = ref('')
const sent = ref(false)
const message = ref('')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    const data = await authService.forgotPassword(email.value)
    message.value = data.message || 'Đã gửi email (nếu tài khoản tồn tại).'
    sent.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Gửi thất bại'
  } finally {
    loading.value = false
  }
}
</script>

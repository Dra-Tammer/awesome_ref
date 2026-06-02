<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const auth = useAuthStore()

const isRegister = ref(false)
const form = ref({ username: '', password: '', confirmPassword: '' })
const error = ref('')
const success = ref('')
const loading = ref(false)
const passwordRef = ref(null)

async function onSubmit() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register(form.value.username, form.value.password, form.value.confirmPassword)
      success.value = '注册成功，请输入密码登录'
      form.value.password = ''
      form.value.confirmPassword = ''
      isRegister.value = false
      await nextTick()
      passwordRef.value?.focus()
    } else {
      await auth.login(form.value.username, form.value.password)
      router.push({ name: 'references' })
    }
  } catch (e) {
    error.value = e.message
  }
  loading.value = false
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>

    <Transition name="slide" mode="out-in" appear>
      <div class="login-card" :key="isRegister">
        <div class="login-header">
          <div class="login-logo">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              <path d="M8 7h8M8 11h6"/>
            </svg>
          </div>
          <h1 class="login-title">AwesomeRef</h1>
          <p class="login-subtitle">{{ isRegister ? '创建您的学术文献管理账户' : '欢迎回来，登录以继续' }}</p>
        </div>

        <form @submit.prevent="onSubmit" class="login-form">
          <div class="form-field">
            <label for="username">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              用户名
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              placeholder="请输入用户名"
              required
              autofocus
            >
          </div>

          <div class="form-field">
            <label for="password">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              密码
            </label>
            <input
              id="password"
              ref="passwordRef"
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              required
            >
          </div>

          <div v-if="isRegister" class="form-field">
            <label for="confirmPassword">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              确认密码
            </label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              required
            >
          </div>

          <transition name="fade">
            <p v-if="success" class="login-success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {{ success }}
            </p>
          </transition>

          <transition name="fade">
            <p v-if="error" class="login-error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              {{ error }}
            </p>
          </transition>

          <button type="submit" class="btn-login" :disabled="loading">
            <span v-if="loading" class="login-spinner"></span>
            <span v-else>{{ isRegister ? '创建账户' : '登录' }}</span>
          </button>
        </form>

        <div class="login-divider">
          <span>{{ isRegister ? '已有账户？' : '还没有账户？' }}</span>
        </div>

        <button class="btn-switch" @click="isRegister = !isRegister; error = ''; success = ''">
          {{ isRegister ? '返回登录' : '注册新账户' }}
        </button>
      </div>
    </Transition>

    <p class="login-footer">AwesomeRef &copy; 2026 &middot; 学术文献管理工具</p>
  </div>
</template>

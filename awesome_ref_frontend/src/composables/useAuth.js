import { ref, computed } from 'vue'

const token = ref('')
const username = ref('')
const logged = ref(false)

// Try to restore session by hitting a protected endpoint
async function tryRestoreSession() {
  try {
    const res = await fetch('/api/groups', { credentials: 'same-origin' })
    if (res.ok) {
      logged.value = true
      return true
    }
  } catch { /* server not running */ }
  return false
}

export function useAuth() {
  const isLoggedIn = computed(() => logged.value)

  function getHeaders() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function login(user, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ username: user, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '登录失败')
    }
    const data = await res.json()
    token.value = data.access_token
    username.value = data.username
    logged.value = true
    return data
  }

  async function register(user, password, confirmPassword) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ username: user, password, confirmPassword }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '注册失败')
    }
    return await res.json()
  }

  function logout() {
    token.value = ''
    username.value = ''
    logged.value = false
  }

  async function changePassword(oldPassword, newPassword, confirmPassword) {
    const res = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getHeaders() },
      credentials: 'same-origin',
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword, confirm_password: confirmPassword }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '修改密码失败')
    }
    return await res.json()
  }

  return {
    token,
    username,
    isLoggedIn,
    getHeaders,
    login,
    register,
    logout,
    changePassword,
    tryRestoreSession,
  }
}

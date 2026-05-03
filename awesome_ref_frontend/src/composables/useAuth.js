import { ref, computed } from 'vue'

const token = ref(localStorage.getItem('auth_token') || '')
const username = ref(localStorage.getItem('auth_username') || '')

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value)

  function getHeaders() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function login(user, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '登录失败')
    }
    const data = await res.json()
    token.value = data.access_token
    username.value = data.username
    localStorage.setItem('auth_token', data.access_token)
    localStorage.setItem('auth_username', data.username)
    return data
  }

  async function register(user, password, confirmPassword) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password, confirmPassword }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '注册失败')
    }
    const data = await res.json()
    token.value = data.access_token
    username.value = data.username
    localStorage.setItem('auth_token', data.access_token)
    localStorage.setItem('auth_username', data.username)
    return data
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_username')
  }

  async function changePassword(oldPassword, newPassword, confirmPassword) {
    const res = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getHeaders() },
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
  }
}

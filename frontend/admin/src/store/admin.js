import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAdminStore = defineStore('admin', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('admin_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value && user.value?.role === 'admin')

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('admin_token', newToken)
  }

  function setUser(newUser) {
    user.value = newUser
    localStorage.setItem('admin_user', JSON.stringify(newUser))
  }

  async function login(credentials) {
    const response = await authApi.login(credentials)
    if (response.user.role !== 'admin') {
      throw new Error('需要管理员权限')
    }
    setToken(response.access_token)
    setUser(response.user)
    return response
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const response = await authApi.getMe()
      if (response.role !== 'admin') {
        logout()
        throw new Error('需要管理员权限')
      }
      setUser(response)
    } catch (error) {
      logout()
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    setToken,
    setUser,
    login,
    logout,
    fetchUser
  }
})

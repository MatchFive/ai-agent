import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUser(newUser) {
    user.value = newUser
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  async function login(credentials) {
    const response = await authApi.login(credentials)
    setToken(response.access_token)
    setUser(response.user)
    return response
  }

  async function register(userData) {
    const response = await authApi.register(userData)
    setToken(response.access_token)
    setUser(response.user)
    return response
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const response = await authApi.getMe()
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
    register,
    logout,
    fetchUser
  }
})

import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    displayName: (s) => s.user?.name || s.user?.username || '',
  },
  actions: {
    async login(username: string, password: string) {
      const res = await api.post('/auth/login', { username, password })
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    async register(username: string, password: string) {
      const res = await api.post('/auth/register', { username, password })
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    async fetchMe() {
      const res = await api.get('/auth/me')
      this.user = res.data
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    async changePassword(oldPassword: string, newPassword: string) {
      await api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword })
    },
    async logout() {
      try { await api.post('/auth/logout') } catch {}
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
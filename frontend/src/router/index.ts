import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('../views/Login.vue') },
    { path: '/register', component: () => import('../views/Register.vue') },
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: () => import('../views/Dashboard.vue') },
    { path: '/record', component: () => import('../views/Record.vue') },
    { path: '/profile', component: () => import('../views/Profile.vue') },
    { path: '/advice', component: () => import('../views/Advice.vue') },
    { path: '/history', component: () => import('../views/History.vue') },
    { path: '/foods', component: () => import('../views/Foods.vue') },
    { path: '/guidelines', component: () => import('../views/Guidelines.vue') },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const publicPages = ['/login', '/register']
  if (!token && !publicPages.includes(to.path)) return '/login'
  if (token && publicPages.includes(to.path)) return '/dashboard'
})

export default router
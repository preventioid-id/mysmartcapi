import { createRouter, createWebHistory } from 'vue-router'

import type { RouteRecordRaw, NavigationGuardNext, RouteLocationNormalized } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('@/pages/Login.vue')
  },
  {
    path: '/interview',
    name: 'Interview',
    component: () => import('@/pages/Interview.vue')
  },
  {
    // PERBAIKAN 1: Path diubah menjadi huruf kecil semua
    path: '/interview-manual',
    name: 'Interview Manual',
    component: () => import('@/pages/InterviewManual.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/pages/Settings.vue')
  },
  {
    path: '/Register',
    name: 'Register',
    component: () => import('@/pages/Register.vue')
  }, // <-- PERBAIKAN 2: Koma yang hilang ditambahkan di sini
  {
    path: '/RegisterVoice',
    name: 'RegisterVoice',
    component: () => import('@/pages/RegisterVoice.vue')
  },
  {
    path: '/forget-password',
    name: 'ForgetPassword',
    component: () => import('@/pages/ForgetPassword.vue')
  },
  {
    path: '/mode-select',
    name: 'ModeSelect',
    component: () => import('@/pages/ModeSelect.vue')
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/pages/ResetPassword.vue')
  },
    {
    path: '/about-us',
    name: 'AboutUs',
    component: () => import('@/pages/AboutUs.vue')
  }
]


const router = createRouter({
  history: createWebHistory(),
  routes
})

// route guard global: cek autentikasi + role
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const requiresAuth = to.meta && (to.meta as any).requiresAuth
  const requiredRole = to.meta && (to.meta as any).requiresRole
  let currentUser: any = null
  try {
    currentUser = JSON.parse(localStorage.getItem('auth_user') || 'null')
  } catch (e) {
    currentUser = null
  }

  if (requiresAuth && !currentUser) {
    // arahkan ke login bila belum login
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (requiredRole) {
    if (!currentUser || currentUser.role !== requiredRole) {
      // akses ditolak
      return next({ path: '/', query: { denied: 'role' } })
    }
  }

  return next()
})

export default router
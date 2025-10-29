import { createRouter, createWebHistory } from 'vue-router'

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
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/pages/ResetPassword.vue')
  }

]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
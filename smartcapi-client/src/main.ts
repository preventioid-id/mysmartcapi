// src/main.ts
import { createApp } from 'vue';
import App from './App.vue';
import { createRouter, createWebHistory } from 'vue-router';
import { createPinia } from 'pinia';

// Impor semua halaman yang dibutuhkan
import Login from './pages/Login.vue';
import Register from './pages/Register.vue';
import RegisterVoice from './pages/RegisterVoice.vue';
import ForgetPassword from './pages/ForgetPassword.vue';
import ModeSelect from './pages/ModeSelect.vue';
import Interview from './pages/Interview.vue';
import InterviewManual from './pages/InterviewManual.vue';
import RekapitulasiPendataan from './pages/RekapitulasiPendataan.vue';
import Settings from './pages/Settings.vue';
import Profile from './pages/Profile.vue'; // <-- 1. PASTIKAN PROFILE.VUE DIIMPOR

const routes = [
  // Alur Utama Sesuai EPC
  { path: '/', component: Login },
  { path: '/register', component: Register },
  { path: '/register-voice', component: RegisterVoice },
  { path: '/forget-password', component: ForgetPassword },
  { path: '/select-mode', component: ModeSelect },
  { path: '/interview', component: Interview },
  { path: '/interview-manual', component: InterviewManual },
  { path: '/rekapitulasi', component: RekapitulasiPendataan },
  
  // Rute tambahan
  { path: '/settings', component: Settings },

  // --- PERBAIKAN DI SINI ---
  // Arahkan /profile ke komponen Profile, bukan Settings
  { path: '/profile', component: Profile }, // <-- 2. UBAH DARI SETTINGS MENJADI PROFILE
];

const router = createRouter({ 
  history: createWebHistory(), 
  routes 
});

const pinia = createPinia();
const app = createApp(App);

app.use(pinia);
app.use(router);

// Register Service Worker untuk offline-first architecture
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then((registration: ServiceWorkerRegistration) => {
        console.log('✅ Service Worker registered:', registration);
        
        // Request notification permission untuk sync notifications
        if ('Notification' in window && Notification.permission === 'default') {
          Notification.requestPermission().then((permission: NotificationPermission) => {
            console.log('📬 Notification permission:', permission);
          });
        }

        // Check for updates periodically
        setInterval(() => {
          registration.update();
        }, 60000); // Check every minute
      })
      .catch((error: Error) => {
        console.error('❌ Service Worker registration failed:', error);
      });
  });

  // Handle service worker updates
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    console.log('🔄 Service Worker updated, reloading page...');
    window.location.reload();
  });
}

app.mount('#app');
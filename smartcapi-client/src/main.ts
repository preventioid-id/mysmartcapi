// src/main.ts
import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // Import the router from router/index.ts
import { createPinia } from 'pinia';

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
// frontend/src/utils/networkMonitor.js
import { ref, readonly } from 'vue';

const isOnline = ref(navigator.onLine);
const connectionType = ref('unknown');
const lastOnlineTime = ref(null);
const lastOfflineTime = ref(null);

// Initialize connection type
if ('connection' in navigator) {
  connectionType.value = navigator.connection.effectiveType || 'unknown';
}

// Event handlers
const handleOnline = () => {
  isOnline.value = true;
  lastOnlineTime.value = new Date();
  console.log('✅ Connection restored at', lastOnlineTime.value);
  
  // Trigger sync when coming back online
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then(registration => {
      if ('sync' in registration) {
        registration.sync.register('transcript-sync');
      }
    });
  }
};

const handleOffline = () => {
  isOnline.value = false;
  lastOfflineTime.value = new Date();
  console.log('❌ Connection lost at', lastOfflineTime.value);
};

const handleConnectionChange = () => {
  if ('connection' in navigator) {
    connectionType.value = navigator.connection.effectiveType || 'unknown';
    console.log('🔄 Connection type changed to', connectionType.value);
  }
};

// Register event listeners
window.addEventListener('online', handleOnline);
window.addEventListener('offline', handleOffline);

if ('connection' in navigator) {
  navigator.connection.addEventListener('change', handleConnectionChange);
}

// Utility functions
export function useNetworkMonitor() {
  const getConnectionQuality = () => {
    const type = connectionType.value;
    if (!isOnline.value) return 'offline';
    
    switch(type) {
      case 'slow-2g':
      case '2g':
        return 'poor';
      case '3g':
        return 'moderate';
      case '4g':
      case '5g':
        return 'good';
      default:
        return 'unknown';
    }
  };

  const checkConnection = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/health', {
        method: 'HEAD',
        cache: 'no-cache'
      });
      return response.ok;
    } catch {
      return false;
    }
  };

  const getDowntimeDuration = () => {
    if (isOnline.value || !lastOfflineTime.value) return 0;
    return Date.now() - lastOfflineTime.value.getTime();
  };

  return {
    // Readonly state
    isOnline: readonly(isOnline),
    connectionType: readonly(connectionType),
    lastOnlineTime: readonly(lastOnlineTime),
    lastOfflineTime: readonly(lastOfflineTime),
    
    // Methods
    getConnectionQuality,
    checkConnection,
    getDowntimeDuration
  };
}

// Auto-sync manager
export class AutoSyncManager {
  constructor(syncCallback, options = {}) {
    this.syncCallback = syncCallback;
    this.retryInterval = options.retryInterval || 30000; // 30 seconds
    this.maxRetries = options.maxRetries || 5;
    this.retryCount = 0;
    this.retryTimer = null;
    
    // Start monitoring
    this.startMonitoring();
  }

  startMonitoring() {
    window.addEventListener('online', () => {
      console.log('📡 Network restored, attempting sync...');
      this.attemptSync();
    });
  }

  async attemptSync() {
    if (!navigator.onLine) {
      console.log('⏸️ Sync postponed: offline');
      return;
    }

    try {
      await this.syncCallback();
      console.log('✅ Auto-sync successful');
      this.retryCount = 0;
      this.clearRetryTimer();
    } catch (error) {
      console.error('❌ Auto-sync failed:', error);
      this.scheduleRetry();
    }
  }

  scheduleRetry() {
    if (this.retryCount >= this.maxRetries) {
      console.log('⚠️ Max retry attempts reached');
      this.retryCount = 0;
      return;
    }

    this.retryCount++;
    console.log(`🔄 Scheduling retry ${this.retryCount}/${this.maxRetries} in ${this.retryInterval/1000}s`);
    
    this.clearRetryTimer();
    this.retryTimer = setTimeout(() => {
      this.attemptSync();
    }, this.retryInterval);
  }

  clearRetryTimer() {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  destroy() {
    this.clearRetryTimer();
  }
}

export default {
  useNetworkMonitor,
  AutoSyncManager
};
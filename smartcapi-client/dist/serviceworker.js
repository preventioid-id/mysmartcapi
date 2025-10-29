const CACHE_NAME = 'smartcapi-v1';
const STATIC_FILES = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/icons/smartcapi-icon.png',
  '/icons/smartcapi-logo.png',
];

const DB_NAME = "smartcapi_local";
const STORE_NAME = "transcripts";

// --- IndexedDB Functions ---
function getPendingTranscripts() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onerror = (event) => reject(event.target.error);
        request.onsuccess = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                resolve([]);
                return;
            }
            const tx = db.transaction(STORE_NAME, "readonly");
            const store = tx.objectStore(STORE_NAME);
            const index = store.index("sync_status");
            const getRequest = index.getAll("pending");
            getRequest.onsuccess = () => resolve(getRequest.result);
            getRequest.onerror = (event) => reject(event.target.error);
        };
    });
}

function updateTranscriptStatus(uuid, status) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onerror = (event) => reject(event.target.error);
        request.onsuccess = (event) => {
            const db = event.target.result;
            const tx = db.transaction(STORE_NAME, "readwrite");
            const store = tx.objectStore(STORE_NAME);
            const getRequest = store.get(uuid);
            getRequest.onsuccess = () => {
                const record = getRequest.result;
                if (record) {
                    record.sync_status = status;
                    const updateRequest = store.put(record);
                    updateRequest.onsuccess = () => resolve();
                    updateRequest.onerror = (e) => reject(e.target.error);
                } else {
                    reject(`Record not found: ${uuid}`);
                }
            };
            getRequest.onerror = (e) => reject(e.target.error);
        };
    });
}

// --- Sync Function ---
async function syncWithServer() {
    console.log('[Service Worker] Attempting to sync...');
    const pendingItems = await getPendingTranscripts();

    if (!pendingItems || pendingItems.length === 0) {
        console.log('[Service Worker] No pending data to sync.');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/api/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: pendingItems }),
        });

        if (!response.ok) throw new Error(`Server responded with ${response.status}`);

        const data = await response.json();
        console.log('[Service Worker] Sync response:', data);

        const promises = data.results.map(result => {
            const newStatus = (result.status === 'created' || result.status === 'updated') ? 'synced' : 'conflict';
            return updateTranscriptStatus(result.uuid, newStatus);
        });

        await Promise.all(promises);
        console.log('[Service Worker] Sync complete.');
    } catch (error) {
        console.error('[Service Worker] Sync failed:', error);
        // Retry will be handled by the browser based on the sync registration
        throw error; // Throwing error signals the sync manager to retry
    }
}

// --- Service Worker Lifecycle ---
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => 
      cache.addAll(STATIC_FILES)
    )
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
    ])
  );
});

self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Strategy 1: Cache-first for static files
  if (STATIC_FILES.some(file => url.pathname.endsWith(file) || url.pathname === file)) {
    event.respondWith(
      caches.match(event.request).then(response => {
        return response || fetch(event.request).then(fetchResponse => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, fetchResponse.clone());
            return fetchResponse;
          });
        });
      }).catch(() => {
        // Return offline page if available
        if (url.pathname === '/' || url.pathname === '/index.html') {
          return caches.match('/offline.html');
        }
      })
    );
    return;
  }

  // Strategy 2: Network-first for API calls with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Clone response to cache successful API calls
          const responseClone = response.clone();
          if (response.ok) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache when offline
          return caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
              console.log('[Service Worker] Serving cached API response for:', url.pathname);
              return cachedResponse;
            }
            // Return error response if no cache available
            return new Response(JSON.stringify({ 
              error: 'Offline - No cached data available',
              offline: true 
            }), {
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            });
          });
        })
    );
    return;
  }

  // Strategy 3: Network-first for all other requests
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request).then(response => {
        return response || caches.match('/offline.html');
      });
    })
  );
});

// --- Background Sync Event ---
self.addEventListener('sync', event => {
  if (event.tag === 'transcript-sync') {
    console.log('[Service Worker] Sync event received for "transcript-sync"');
    event.waitUntil(syncWithServer());
  }
});

// --- Periodic Background Sync (if supported) ---
self.addEventListener('periodicsync', event => {
  if (event.tag === 'transcript-periodic-sync') {
    console.log('[Service Worker] Periodic sync triggered');
    event.waitUntil(syncWithServer());
  }
});

// --- Push Notifications (optional for future features) ---
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'Data berhasil disinkronisasi',
    icon: '/icons/smartcapi-icon.png',
    badge: '/icons/smartcapi-icon.png',
    vibrate: [200, 100, 200]
  };
  
  event.waitUntil(
    self.registration.showNotification('SmartCAPI', options)
  );
});
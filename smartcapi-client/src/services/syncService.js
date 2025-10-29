
import { getPendingTranscripts, updateTranscriptStatus } from './localDb';

async function syncWithServer() {
    console.log('Attempting to sync with server...');
    const pendingItems = await getPendingTranscripts();

    if (!pendingItems || pendingItems.length === 0) {
        console.log('No pending data to sync.');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/api/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ items: pendingItems }),
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const data = await response.json();
        console.log('Sync response from server:', data);

        // Update local status based on server response
        const promises = data.results.map(result => {
            if (result.status === 'created' || result.status === 'updated') {
                return updateTranscriptStatus(result.uuid, 'synced');
            } else if (result.status === 'conflict') {
                return updateTranscriptStatus(result.uuid, 'conflict');
            }
        });

        await Promise.all(promises);
        console.log('Sync done: Local database updated.');

    } catch (error) {
        console.error('Sync failed:', error);
        // The data will remain in 'pending' state and will be retried on the next sync event.
    }
}

// Function to be called from the main app to register a background sync
async function registerBackgroundSync() {
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
        try {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('transcript-sync');
            console.log('Background sync registered');
        } catch (error) {
            console.error('Background sync registration failed:', error);
        }
    } else {
        console.log('Background Sync not supported. Trying a direct sync.');
        // Fallback for browsers that don't support Background Sync
        await syncWithServer();
    }
}

export { syncWithServer, registerBackgroundSync };

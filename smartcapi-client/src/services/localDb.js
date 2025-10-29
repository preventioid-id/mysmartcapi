
const DB_NAME = "smartcapi_local";
const STORE_NAME = "transcripts";
let db;

function initDB() {
    return new Promise((resolve, reject) => {
        if (db) {
            return resolve(db);
        }
        const request = indexedDB.open(DB_NAME, 1);

        request.onerror = (event) => {
            console.error("IndexedDB error:", event.target.error);
            reject("Error opening database.");
        };

        request.onsuccess = (event) => {
            db = event.target.result;
            resolve(db);
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                const store = db.createObjectStore(STORE_NAME, { keyPath: "uuid" });
                store.createIndex("sync_status", "sync_status", { unique: false });
            }
        };
    });
}

async function saveTranscript(speaker_id, text) {
    const db = await initDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);

    const record = {
        uuid: self.crypto.randomUUID(),
        speaker_id: speaker_id,
        text: text,
        updated_at: Date.now() / 1000, // Unix timestamp in seconds
        sync_status: "pending",
    };

    await store.put(record);
    return tx.complete;
}

async function getPendingTranscripts() {
    const db = await initDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const index = store.index("sync_status");
    const request = index.getAll("pending");

    return new Promise((resolve, reject) => {
        request.onsuccess = () => {
            resolve(request.result);
        };
        request.onerror = (event) => {
            console.error("Error fetching pending transcripts:", event.target.error);
            reject("Error fetching data.");
        };
    });
}

async function updateTranscriptStatus(uuid, status) {
    const db = await initDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const request = store.get(uuid);

    return new Promise((resolve, reject) => {
        request.onsuccess = () => {
            const record = request.result;
            if (record) {
                record.sync_status = status;
                const updateRequest = store.put(record);
                updateRequest.onsuccess = () => resolve();
                updateRequest.onerror = (event) => reject(event.target.error);
            } else {
                reject("Record not found.");
            }
        };
        request.onerror = (event) => reject(event.target.error);
    });
}

export { initDB, saveTranscript, getPendingTranscripts, updateTranscriptStatus };

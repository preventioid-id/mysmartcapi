<template>
  <div>
    <div class="container interview-page">
      <button class="back-btn" @click="goBack">&lt;&lt; Kembali</button>

      <div class="form-title">Wawancara dengan Asistensi AI</div>

      <form @submit.prevent="openSubmitDialog" class="interview-form">
        <div v-for="q in questions" :key="q.key" class="question-block">
          <label :for="q.key">{{ q.label }}</label>
          <select
            v-if="q.type === 'select'"
            :id="q.key"
            v-model="manualForm[q.key]"
            class="form-input"
          >
            <option disabled value="">Pilih Pendidikan</option>
            <option v-for="option in q.options" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
          <input
            v-else
            :id="q.key"
            v-model="manualForm[q.key]"
            :type="q.type || 'text'"
            class="form-input"
            :placeholder="q.key === 'tanggal_lahir' ? 'dd/mm/yyyy' : ''"
            @blur="q.key === 'tanggal_lahir' ? handleDateBlur : null"
          />
        </div>
      </form>

      <div class="bottom-action-bar">
        <button type="button" class="action-btn clear-btn" @click="handleClear">
          CLEAR DATA
        </button>
        <div class="mic-container">
          <div class="mic-button" :class="{ recording: isRecording }" @click="handleMic">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" fill="white"/>
              <path d="M19 12H17C17 14.76 14.76 17 12 17C9.24 17 7 14.76 7 12H5C5 15.54 7.72 18.45 11 18.93V22H13V18.93C16.28 18.45 19 15.54 19 12Z" fill="white"/>
            </svg>
          </div>
          <div v-if="isRecording" class="duration-display">{{ formattedDuration }}</div>
        </div>
        <button type="button" class="action-btn submit-btn" @click="openSubmitDialog">
          SUBMIT
        </button>
      </div>

      <div v-if="showSubmitDialog" class="dialog-overlay">
        <div class="dialog-box">
          <p>Apakah Anda yakin ingin mengirim data wawancara ini?</p>
          <div class="dialog-actions">
            <button class="dialog-btn confirm-btn" @click="confirmSubmit">YA</button>
            <button class="dialog-btn cancel-btn" @click="cancelSubmit">TIDAK</button>
          </div>
        </div>
      </div>

      <!-- Sync Status Indicator (NEW) -->
      <div v-if="syncStatus" class="sync-status" :class="syncStatus">
        <span v-if="syncStatus === 'saving'">💾 Menyimpan data lokal...</span>
        <span v-if="syncStatus === 'saved'">✅ Data tersimpan lokal</span>
        <span v-if="syncStatus === 'syncing'">🔄 Mengirim ke server...</span>
        <span v-if="syncStatus === 'synced'">✅ Data berhasil tersinkronisasi</span>
        <span v-if="syncStatus === 'error'">⚠️ Gagal sinkronisasi (akan coba lagi)</span>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useInterviewStore } from '../store/interview';
import axios from 'axios'; // Impor axios untuk mengirim data

const router = useRouter();
const interviewStore = useInterviewStore();

const questions = [
  { key: 'nama', label: 'Nama' },
  { key: 'alamat', label: 'Alamat' },
  { key: 'tempat_lahir', label: 'Tempat Lahir' },
  { key: 'tanggal_lahir', label: 'Tanggal Lahir', type: 'text' },
  { key: 'usia', label: 'Usia', type: 'number' },
  {
    key: 'pendidikan',
    label: 'Pendidikan',
    type: 'select',
    options: [
      "Tidak/Belum Bersekolah", "SD", "SMP", "SMA", "Perguruan Tinggi"
    ]
  },
  { key: 'pekerjaan', label: 'Pekerjaan' },
  { key: 'hobi', label: 'Hobi' },
  { key: 'nomor_telepon', label: 'Nomor Telepon' },
  { key: 'alamat_email', label: 'Alamat Email', type: 'email' },
];

const manualForm = ref(Object.fromEntries(questions.map(q => [q.key, ""])));
const showSubmitDialog = ref(false);
const isRecording = ref(false);
const timer = ref(null);
const durationInSeconds = ref(0);

// State baru untuk MediaRecorder
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const audioBlob = ref(null);

// ===== STATE BARU UNTUK OFFLINE-FIRST =====
const syncStatus = ref(''); // saving, saved, syncing, synced, error
const DB_NAME = 'smartcapi_local';
const STORE_NAME = 'transcripts';
// ===========================================

const formattedDuration = computed(() => {
  const minutes = Math.floor(durationInSeconds.value / 60);
  const seconds = durationInSeconds.value % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
});

function goBack() {
  router.push('/rekapitulasi');
}

function openSubmitDialog() {
  showSubmitDialog.value = true;
}

// ===== FUNGSI BARU: INIT INDEXEDDB =====
function initDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const objectStore = db.createObjectStore(STORE_NAME, { keyPath: 'uuid' });
        objectStore.createIndex('sync_status', 'sync_status', { unique: false });
        objectStore.createIndex('timestamp', 'timestamp', { unique: false });
        objectStore.createIndex('interview_id', 'interview_id', { unique: false });
        console.log('📦 IndexedDB initialized');
      }
    };
  });
}

// ===== FUNGSI BARU: SIMPAN KE INDEXEDDB =====
async function saveToIndexedDB(interviewData) {
  try {
    syncStatus.value = 'saving';
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      
      const record = {
        ...interviewData,
        uuid: crypto.randomUUID(),
        sync_status: 'pending',
        timestamp: new Date().toISOString(),
        last_modified: new Date().toISOString()
      };
      
      const request = store.put(record);
      
      request.onsuccess = () => {
        syncStatus.value = 'saved';
        console.log('✅ Data saved to IndexedDB:', record.uuid);
        setTimeout(() => syncStatus.value = '', 3000); // Clear after 3s
        resolve(record);
      };
      
      request.onerror = () => {
        syncStatus.value = 'error';
        console.error('❌ Failed to save to IndexedDB:', request.error);
        reject(request.error);
      };
    });
  } catch (error) {
    syncStatus.value = 'error';
    console.error('❌ IndexedDB error:', error);
    throw error;
  }
}

// ===== FUNGSI BARU: KONVERSI BLOB KE BASE64 =====
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// ===== FUNGSI BARU: REQUEST BACKGROUND SYNC =====
async function requestBackgroundSync() {
  if ('serviceWorker' in navigator && 'sync' in self.registration) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('transcript-sync');
      console.log('🔄 Background sync registered');
    } catch (error) {
      console.error('❌ Background sync registration failed:', error);
    }
  }
}

async function confirmSubmit() {
  showSubmitDialog.value = false;

  const emptyFields = questions.filter(q => !manualForm.value[q.key] || !String(manualForm.value[q.key]).trim());
  if (emptyFields.length > 0) {
    alert('Mohon lengkapi semua field yang kosong sebelum mengirim data.');
    return;
  }

  const startTime = interviewStore.interviewStartTime;
  let totalDuration = 0;
  if (startTime > 0) {
    totalDuration = Math.round((Date.now() - startTime) / 1000);
  }

  // ===== MODIFIKASI: SIAPKAN DATA UNTUK INDEXEDDB =====
  const interviewData = {
    ...manualForm.value,
    duration: totalDuration,
    mode: 'AI',
    has_recording: audioBlob.value ? '1' : '0',
    audio_base64: audioBlob.value ? await blobToBase64(audioBlob.value) : null,
    audio_filename: audioBlob.value ? `recording-${Date.now()}.webm` : null
  };

  // ===== STEP 1: SIMPAN KE INDEXEDDB DULU (OFFLINE-FIRST) =====
  try {
    const savedRecord = await saveToIndexedDB(interviewData);
    console.log('💾 Data saved locally with UUID:', savedRecord.uuid);
  } catch (error) {
    console.error('❌ Failed to save locally:', error);
    alert('Gagal menyimpan data lokal. Silakan coba lagi.');
    return;
  }

  // ===== STEP 2: COBA KIRIM KE SERVER (JIKA ONLINE) =====
  if (navigator.onLine) {
    try {
      syncStatus.value = 'syncing';
      
      const formData = new FormData();
      for (const key in manualForm.value) {
        formData.append(key, manualForm.value[key]);
      }
      formData.append('duration', totalDuration);
      formData.append('mode', 'AI');

      if (audioBlob.value) {
        formData.append('has_recording', '1');
        formData.append('audio_file', audioBlob.value, `recording-${Date.now()}.webm`);
      } else {
        formData.append('has_recording', '0');
      }

      const response = await axios.post('http://127.0.0.1:8000/api/interviews', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      console.log('✅ Server response:', response.data);
      syncStatus.value = 'synced';
      
      setTimeout(() => {
        alert(`Data berhasil disubmit dan tersinkronisasi! Durasi: ${totalDuration} detik.`);
        interviewStore.clearInterviewTimer();
        router.push('/rekapitulasi');
      }, 1500);
      
    } catch (error) {
      console.error("⚠️ Gagal mengirim ke server:", error);
      syncStatus.value = 'error';
      
      // Registrasi background sync untuk retry otomatis
      await requestBackgroundSync();
      
      setTimeout(() => {
        alert("Data tersimpan lokal. Akan otomatis tersinkronisasi saat koneksi tersedia.");
        interviewStore.clearInterviewTimer();
        router.push('/rekapitulasi');
      }, 2000);
    }
  } else {
    // ===== JIKA OFFLINE: LANGSUNG KE REKAPITULASI =====
    console.log('📴 Offline mode: Data saved locally');
    await requestBackgroundSync();
    
    setTimeout(() => {
      alert("Anda sedang offline. Data tersimpan lokal dan akan otomatis tersinkronisasi saat koneksi tersedia.");
      interviewStore.clearInterviewTimer();
      router.push('/rekapitulasi');
    }, 1500);
  }
}

function cancelSubmit() {
  showSubmitDialog.value = false;
}

function handleClear() {
  if (confirm('Yakin ingin menghapus semua data?')) {
    Object.keys(manualForm.value).forEach(key => manualForm.value[key] = "");
    audioBlob.value = null;
  }
}

function formatDateToDDMMYYYY(isoDate) {
  if (!isoDate || !isoDate.includes('-')) return isoDate;
  const [yyyy, mm, dd] = isoDate.split('-');
  return `${dd.padStart(2, '0')}/${mm.padStart(2, '0')}/${yyyy}`;
}

function handleDateBlur(e) {
  const val = e.target.value;
  if (val.match(/^\d{4}-\d{2}-\d{2}$/)) {
    manualForm.value.tanggal_lahir = formatDateToDDMMYYYY(val);
  }
}

async function handleMic() {
  if (isRecording.value) {
    if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
      mediaRecorder.value.stop();
    }
    clearInterval(timer.value);
    isRecording.value = false;
  } else {
    try {
      // ===== CEK BROWSER SUPPORT =====
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Browser Anda tidak mendukung perekaman audio. Gunakan Chrome di Android atau Safari iOS 14.3+ dengan HTTPS.');
        return;
      }

      // ===== CEK MEDIARECORDER SUPPORT =====
      if (typeof MediaRecorder === 'undefined') {
        alert('MediaRecorder tidak tersedia. Pastikan Anda menggunakan HTTPS dan browser yang kompatibel.');
        return;
      }

      // ===== REQUEST MICROPHONE PERMISSION =====
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      audioBlob.value = null;
      audioChunks.value = [];
      
      // ===== PILIH FORMAT YANG DIDUKUNG =====
      let mimeType = 'audio/webm';
      const supportedTypes = [
        'audio/webm',
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/mpeg'
      ];
      
      for (const type of supportedTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type;
          break;
        }
      }
      
      console.log('📝 Using MIME type:', mimeType);
      
      mediaRecorder.value = new MediaRecorder(stream, { mimeType });
      
      mediaRecorder.value.ondataavailable = event => {
        if (event.data && event.data.size > 0) {
          audioChunks.value.push(event.data);
        }
      };
      
      mediaRecorder.value.onstop = () => {
        audioBlob.value = new Blob(audioChunks.value, { type: mimeType });
        stream.getTracks().forEach(track => track.stop());
        console.log("✅ Rekaman selesai:", audioBlob.value.size, "bytes");
        
        // Show success feedback for mobile
        if ('vibrate' in navigator) {
          navigator.vibrate(200); // Vibrate for 200ms
        }
      };
      
      mediaRecorder.value.onerror = (event) => {
        console.error('❌ MediaRecorder error:', event.error);
        alert('Terjadi kesalahan saat merekam. Coba lagi.');
        stream.getTracks().forEach(track => track.stop());
        isRecording.value = false;
      };
      
      // ===== START RECORDING =====
      mediaRecorder.value.start(1000); // Collect data every 1 second
      isRecording.value = true;
      durationInSeconds.value = 0;
      timer.value = setInterval(() => durationInSeconds.value++, 1000);
      
      console.log("🎙️ Mulai merekam...");
      
      // Vibrate on start (mobile only)
      if ('vibrate' in navigator) {
        navigator.vibrate(100);
      }
      
    } catch (err) {
      console.error("❌ Gagal mengakses mikrofon:", err);
      
      // Specific error messages
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        alert('Akses mikrofon ditolak. Mohon izinkan akses mikrofon di pengaturan browser Anda.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        alert('Mikrofon tidak ditemukan. Pastikan perangkat Anda memiliki mikrofon.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        alert('Mikrofon sedang digunakan aplikasi lain. Tutup aplikasi tersebut dan coba lagi.');
      } else if (err.name === 'OverconstrainedError') {
        alert('Pengaturan audio tidak didukung. Menggunakan pengaturan default...');
        // Retry with default settings
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          // Continue with simplified setup...
        } catch (retryErr) {
          alert('Tetap gagal. Gunakan browser lain atau periksa pengaturan perangkat.');
        }
      } else {
        alert(`Error: ${err.message || 'Tidak dapat mengakses mikrofon'}`);
      }
    }
  }
}
</script>

<style scoped>
/* Style tidak berubah */
.back-btn { align-self: flex-start; margin-bottom: 20px; background-color: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 20px; font-weight: 600; cursor: pointer; transition: background-color 0.2s; }
.back-btn:hover { background-color: #0056b3; }
.interview-page { max-width: 400px; margin: 0 auto; padding: 20px; background: #ffffff; min-height: 100vh; box-sizing: border-box; position: relative; padding-bottom: 120px; display: flex; flex-direction: column; }
.form-title { text-align: center; color: #1155cc; font-size: 18px; font-weight: 600; margin-bottom: 30px; margin-top: 0; }
.interview-form { display: flex; flex-direction: column; gap: 20px; }
.question-block { display: flex; flex-direction: column; gap: 8px; }
label { font-weight: 500; color: #333; font-size: 14px; }
.form-input { padding: 12px 16px; border: none; border-radius: 8px; background: #f5f5f5; font-size: 14px; outline: none; transition: background-color 0.2s; }
.form-input:focus { background: #eeeeee; }
.bottom-action-bar { position: fixed; left: 0; right: 0; bottom: 0; background: #ffffff; padding: 20px; display: flex; justify-content: center; align-items: center; gap: 40px; box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1); z-index: 1000; }
.action-btn { padding: 12px 24px; border: none; border-radius: 25px; font-weight: 600; font-size: 12px; cursor: pointer; min-width: 100px; transition: all 0.2s; }
.clear-btn { background: #dc3545; color: white; }
.clear-btn:hover { background: #c82333; }
.submit-btn { background: #007bff; color: white; }
.submit-btn:hover { background: #0056b3; }
.mic-container { display: flex; flex-direction: column; justify-content: center; align-items: center; }
.mic-button { width: 60px; height: 60px; background: #007bff; border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: all 0.2s; border: none; outline: none; }
.mic-button:hover { background: #0056b3; transform: scale(1.05); }
.mic-button:active { transform: scale(0.95); }
.mic-button.recording { background: #dc3545; }
.mic-button.recording:hover { background: #c82333; }
.duration-display { margin-top: 8px; font-size: 14px; font-weight: 600; color: #333; font-family: 'monospace'; position: absolute; bottom: 100px; }
@media (max-width: 480px) { .interview-page { max-width: 100vw; padding: 16px; padding-bottom: 120px; } .form-title { font-size: 16px; margin-bottom: 25px; } .bottom-action-bar { gap: 20px; padding: 16px; } .action-btn { min-width: 80px; padding: 10px 16px; font-size: 11px; } .mic-button { width: 50px; height: 50px; } .mic-button svg { width: 20px; height: 20px; } .duration-display { bottom: 90px; } }
.dialog-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); display: flex; justify-content: center; align-items: center; z-index: 2000; }
.dialog-box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); text-align: center; max-width: 350px; width: 90%; }
.dialog-box p { font-size: 1.1rem; margin-bottom: 25px; color: #333; }
.dialog-actions { display: flex; justify-content: center; gap: 20px; }
.dialog-btn { padding: 12px 25px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; transition: background-color 0.2s, transform 0.1s; }
.dialog-btn:hover { transform: translateY(-2px); }
.confirm-btn { background-color: #28a745; color: white; }
.confirm-btn:hover { background-color: #218838; }
.cancel-btn { background-color: #dc3545; color: white; }
.cancel-btn:hover { background-color: #c82333; }

/* ===== STYLE BARU UNTUK SYNC STATUS ===== */
.sync-status {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  z-index: 3000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.sync-status.saving,
.sync-status.syncing {
  background: #ffc107;
  color: #000;
}

.sync-status.saved,
.sync-status.synced {
  background: #28a745;
  color: white;
}

.sync-status.error {
  background: #dc3545;
  color: white;
}
/* ======================================== */
</style>
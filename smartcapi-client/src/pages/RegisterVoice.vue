<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-title">Registrasi Akun</div>
      <p class="instruction">
        Mohon rekam suara anda dengan jelas untuk proses verifikasi. Ucapkan kalimat berikut:
      </p>

      <div class="sample-text" v-html="dynamicSampleText"></div>

      <div class="recorder-section">
        <div class="mic-button" @click="toggleRecording" :class="{ 'is-recording': isRecording }">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" />
            <path d="M19 12H17C17 14.76 14.76 17 12 17C9.24 17 7 14.76 7 12H5C5 15.54 7.72 18.45 11 18.93V22H13V18.93C16.28 18.45 19 15.54 19 12Z" />
          </svg>
        </div>
        <div v-if="isRecording" class="duration-display">{{ formattedDuration }}</div>
        <p :class="['status-text', { 'success': recordingDone }]">{{ statusText }}</p>
      </div>

      <div class="form-buttons">
        <button type="button" class="btn-back" @click="goBack">
          BACK
        </button>
        <button type="submit" class="btn-next" @click="finishRegistration" :disabled="!recordingDone">
          NEXT
        </button>
      </div>

      <!-- Sync Status Indicator (NEW) -->
      <div v-if="syncStatus" class="sync-status" :class="syncStatus">
        <span v-if="syncStatus === 'saving'">💾 Menyimpan rekaman...</span>
        <span v-if="syncStatus === 'saved'">✅ Rekaman tersimpan lokal</span>
        <span v-if="syncStatus === 'uploading'">🔄 Mengirim rekaman...</span>
        <span v-if="syncStatus === 'uploaded'">✅ Rekaman berhasil dikirim</span>
        <span v-if="syncStatus === 'error'">⚠️ Gagal mengirim (akan coba lagi)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
// import { useUserStore } from '../store/user'; 

const isRecording = ref(false);
const recordingDone = ref(false);
const statusText = ref('Tekan untuk merekam');
const router = useRouter();

// ---- STATE BARU UNTUK TIMER ----
const durationInSeconds = ref(0);
const timerInterval = ref(null);
// --------------------------------

// ===== STATE BARU UNTUK AUDIO DAN OFFLINE-FIRST =====
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const audioBlob = ref(null);
const syncStatus = ref(''); // saving, saved, uploading, uploaded, error
const DB_NAME = 'smartcapi_local';
const STORE_NAME = 'voice_registrations';
// ====================================================

// const userStore = useUserStore();
// const registrationData = userStore.registrationData;
const registrationData = { fullName: 'Budi Sanjaya' }; 

// ---- COMPUTED PROPERTY BARU UNTUK FORMAT DURASI ----
const formattedDuration = computed(() => {
  const minutes = Math.floor(durationInSeconds.value / 60);
  const seconds = durationInSeconds.value % 60;
  const paddedMinutes = String(minutes).padStart(2, '0');
  const paddedSeconds = String(seconds).padStart(2, '0');
  return `${paddedMinutes}:${paddedSeconds}`;
});
// ----------------------------------------------------

const dynamicSampleText = computed(() => {
  const userName = registrationData.fullName || '[Nama Anda]';

  return `
    "<br><strong>[Ucapkan Salam]</strong>
    Nama saya <strong>${userName}</strong>. Saya berasal dari [kota asal] dan saat ini berusia [usia
    Anda] tahun. Saya adalah seorang [jenis kelamin Anda], dan saya tinggal di [alamat
    lengkap Anda].
    <br>
    Saya menyelesaikan pendidikan terakhir saya di [nama institusi pendidikan], dengan
    gelar [gelar akademik]. Pendidikan ini telah memberikan saya pengetahuan dan
    keterampilan yang sangat berguna dalam berbagai aspek kehidupan.
    <br> Saat ini, saya bekerja sebagai [posisi pekerjaan Anda] di [nama
    perusahaan/organisasi tempat Anda bekerja]. Dalam pekerjaan saya, saya
    bertanggung jawab atas [deskripsi tugas utama Anda]. Pengalaman kerja ini telah
    mengajarkan saya banyak hal tentang profesionalisme, kerjasama tim, dan tanggung
    jawab.
    <br> Saya sudah menikah dan memiliki [sebutkan jika memiliki anak atau tidak, dan
    berapa jumlahnya jika ada]. Keluarga saya sangat mendukung segala aktivitas dan
    aspirasi saya, termasuk keinginan saya untuk menjadi petugas pendata di BPS.
    <br> Alasan utama saya ingin menjadi petugas pendata BPS adalah karena saya percaya
    bahwa data yang akurat dan terpercaya sangat penting untuk pembangunan negara.
    Sebagai petugas pendata, saya akan memiliki kesempatan untuk berkontribusi
    langsung dalam pengumpulan data yang nantinya akan digunakan untuk merumuskan
    kebijakan-kebijakan penting.
    <br>Saya juga ingin terlibat lebih dalam dengan masyarakat dan membantu memastikan
    bahwa suara mereka terwakili dalam data yang dikumpulkan. Dengan bekerja sebagai
    petugas pendata, saya berharap bisa memberikan dampak positif bagi komunitas
    saya dan bagi Indonesia secara keseluruhan.
    <br>Terima kasih atas kesempatan untuk memperkenalkan diri. Saya sangat berharap
    dapat berkontribusi sebagai petugas pendata BPS dan bekerja sama dengan tim yang
    berdedikasi untuk menciptakan data yang akurat dan bermanfaat.
    Salam hormat,
    <br><strong>${userName}</strong>"
  `;
});

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
        objectStore.createIndex('user_name', 'user_name', { unique: false });
        console.log('📦 Voice Registration IndexedDB initialized');
      }
    };
  });
}

// ===== FUNGSI BARU: SIMPAN VOICE KE INDEXEDDB =====
async function saveVoiceToIndexedDB(voiceData) {
  try {
    syncStatus.value = 'saving';
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      
      const record = {
        ...voiceData,
        uuid: crypto.randomUUID(),
        sync_status: 'pending',
        timestamp: new Date().toISOString(),
        last_modified: new Date().toISOString()
      };
      
      const request = store.put(record);
      
      request.onsuccess = () => {
        syncStatus.value = 'saved';
        console.log('✅ Voice saved to IndexedDB:', record.uuid);
        setTimeout(() => syncStatus.value = '', 2000);
        resolve(record);
      };
      
      request.onerror = () => {
        syncStatus.value = 'error';
        console.error('❌ Failed to save voice to IndexedDB:', request.error);
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
      await registration.sync.register('voice-sync');
      console.log('🔄 Background voice sync registered');
    } catch (error) {
      console.error('❌ Background sync registration failed:', error);
    }
  }
}

async function toggleRecording() {
  if (isRecording.value) {
    // ---- LOGIKA STOP MEREKAM ----
    if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
      mediaRecorder.value.stop();
    }
    clearInterval(timerInterval.value); // Hentikan interval timer
    isRecording.value = false;
    recordingDone.value = true;
    statusText.value = 'Rekaman Selesai. Tekan NEXT untuk melanjutkan.';
    console.log('Rekaman dihentikan oleh pengguna.');
  } else {
    // ---- LOGIKA MULAI MEREKAM ----
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      audioBlob.value = null;
      audioChunks.value = [];
      mediaRecorder.value = new MediaRecorder(stream);
      
      mediaRecorder.value.ondataavailable = event => {
        audioChunks.value.push(event.data);
      };
      
      mediaRecorder.value.onstop = () => {
        audioBlob.value = new Blob(audioChunks.value, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        console.log("✅ Rekaman selesai dan disimpan sebagai Blob.", audioBlob.value);
        notificationStore.notify('rekaman suara Anda telah terekam dalam memori internal perangkat', 'success');
      };
      
      mediaRecorder.value.start();
      isRecording.value = true;
      recordingDone.value = false;
      statusText.value = 'Merekam... Tekan lagi untuk berhenti.';
      console.log('Mulai merekam suara...');
      
      durationInSeconds.value = 0; // Reset durasi ke 0
      timerInterval.value = setInterval(() => {
        durationInSeconds.value++; // Tambah durasi setiap detik
      }, 1000);

      setTimeout(() => {
        if (isRecording.value && mediaRecorder.value.state === 'recording') {
          mediaRecorder.value.stop();
          clearInterval(timerInterval.value); // Hentikan interval timer
          isRecording.value = false;
          recordingDone.value = true;
          statusText.value = 'Rekaman Selesai. Tekan NEXT untuk melanjutkan.';
          console.log('Rekaman selesai (otomatis).');
        }
      }, 10000);
      
    } catch (err) {
      console.error("❌ Gagal mengakses mikrofon:", err);
      alert("Tidak dapat mengakses mikrofon. Pastikan Anda telah memberikan izin.");
    }
  }
}

async function finishRegistration() {
  if (!audioBlob.value) {
    alert('Mohon rekam suara Anda terlebih dahulu.');
    return;
  }

  console.log('Mengirim rekaman suara dan menyelesaikan pendaftaran...');

  // ===== STEP 1: SIAPKAN DATA VOICE =====
  const voiceData = {
    user_name: registrationData.fullName,
    audio_base64: await blobToBase64(audioBlob.value),
    audio_filename: `voice-${Date.now()}.webm`,
    duration: durationInSeconds.value,
    registration_type: 'voice_verification'
  };

  // ===== STEP 2: SIMPAN KE INDEXEDDB DULU (OFFLINE-FIRST) =====
  try {
    const savedRecord = await saveVoiceToIndexedDB(voiceData);
    console.log('💾 Voice saved locally with UUID:', savedRecord.uuid);
  } catch (error) {
    console.error('❌ Failed to save voice locally:', error);
    alert('Gagal menyimpan rekaman lokal. Silakan coba lagi.');
    return;
  }

  // ===== STEP 3: COBA KIRIM KE SERVER (JIKA ONLINE) =====
  if (navigator.onLine) {
    try {
      syncStatus.value = 'uploading';
      
      const formData = new FormData();
      formData.append('upload_type', 'voice_registration');
      formData.append('name', registrationData.fullName);
      formData.append('mode', 'AI');
      formData.append('has_recording', '1');
      formData.append('audio_file', audioBlob.value, `voice-${Date.now()}.webm`);
      formData.append('duration', durationInSeconds.value);
      
      const response = await fetch('http://127.0.0.1:8000/api/interviews', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      
      const data = await response.json();
      console.log('✅ Server response:', data);
      syncStatus.value = 'uploaded';
      
      setTimeout(() => {
        alert('Akun Anda berhasil dibuat dan rekaman suara tersimpan!');
        router.push('/');
      }, 1500);
      
    } catch (error) {
      console.error("⚠️ Gagal mengirim rekaman ke server:", error);
      syncStatus.value = 'error';
      
      // Registrasi background sync untuk retry otomatis
      await requestBackgroundSync();
      
      setTimeout(() => {
        alert('Akun dibuat! Rekaman tersimpan lokal dan akan otomatis dikirim saat koneksi tersedia.');
        router.push('/');
      }, 2000);
    }
  } else {
    // ===== JIKA OFFLINE: LANGSUNG KE LOGIN =====
    console.log('📴 Offline mode: Voice saved locally');
    await requestBackgroundSync();
    
    setTimeout(() => {
      alert('Akun dibuat! Anda sedang offline. Rekaman akan otomatis dikirim saat koneksi tersedia.');
      router.push('/');
    }, 1500);
  }
}

function goBack() {
  router.back();
}
</script>
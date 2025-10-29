<template>
  <div>
    <div class="container interview-page">
      <button class="back-btn" @click="goBack">&lt;&lt; Kembali</button>

      <div class="form-title">Wawancara tanpa Asistensi AI</div>

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
          />
        </div>
      </form>

      <div class="bottom-action-bar">
        <button type="button" class="action-btn clear-btn" @click="handleClear">
          CLEAR DATA
        </button>
        <div class="duration-display">{{ displayedDuration }}</div>
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

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
// Impor store untuk durasi
import { useInterviewStore } from '../store/interview';

const router = useRouter();
// Inisialisasi store durasi
const interviewStore = useInterviewStore();

const displayedDuration = ref('00:00');
let timerInterval = null;

onMounted(() => {

  timerInterval = setInterval(() => {
    const startTime = interviewStore.interviewStartTime;
    if (startTime > 0) {
      const now = Date.now();
      const elapsedSeconds = Math.round((now - startTime) / 1000);
      const minutes = Math.floor(elapsedSeconds / 60);
      const seconds = elapsedSeconds % 60;
      displayedDuration.value = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
  }, 1000);
});

onUnmounted(() => {
  clearInterval(timerInterval);
});

const questions = [
  { key: 'nama', label: 'Nama' },
  { key: 'alamat', label: 'Alamat' },
  { key: 'tempat_lahir', label: 'Tempat Lahir' },
  { key: 'tanggal_lahir', label: 'Tanggal Lahir', type: 'date' },
  { key: 'usia', label: 'Usia', type: 'number' },
  { 
    key: 'pendidikan', 
    label: 'Pendidikan', 
    type: 'select', 
    options: [
      "Tidak/Belum Bersekolah",
      "SD",
      "SMP",
      "SMA",
      "Perguruan Tinggi"
    ] 
  },
  { key: 'pekerjaan', label: 'Pekerjaan' },
  { key: 'hobi', label: 'Hobi' },
  { key: 'nomor_telepon', label: 'Nomor Telepon' },
  { key: 'alamat_email', label: 'Alamat Email', type: 'email' },
];

const manualForm = ref(Object.fromEntries(questions.map(q => [q.key, ""])));
const showSubmitDialog = ref(false); // State untuk mengontrol dialog

watch(() => manualForm.value.tanggal_lahir, (newDate) => {
  if (newDate) {
    const birthDate = new Date(newDate);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDifference = today.getMonth() - birthDate.getMonth();
    if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    manualForm.value.usia = age >= 0 ? age : '';
  } else {
    manualForm.value.usia = '';
  }
});

function goBack() {
  router.push('/rekapitulasi');
}

// PERUBAHAN: Membuka dialog konfirmasi
function openSubmitDialog() {
  showSubmitDialog.value = true;
}

// PERUBAHAN: Fungsi ketika user mengklik 'YA'
function confirmSubmit() {
  showSubmitDialog.value = false; // Tutup dialog
  const emptyFields = questions.filter(q => !manualForm.value[q.key] || !String(manualForm.value[q.key]).trim());
  if (emptyFields.length > 0) {
    alert('Mohon lengkapi semua field yang kosong sebelum mengirim data.');
    return;
  }

  // Logika penghitungan durasi dari Kode B1
  const startTime = interviewStore.interviewStartTime;
  let durationInSeconds = 0;
  if (startTime > 0) {
    const endTime = Date.now();
    durationInSeconds = Math.round((endTime - startTime) / 1000);
  }

  const submissionData = {
    ...manualForm.value,
    duration: durationInSeconds,
  };

  // Panggil action dari store untuk menyimpan data
  interviewStore.addManualInterview(submissionData);

  // Bersihkan timer setelah selesai
  interviewStore.clearInterviewTimer();

  // Beri notifikasi dan arahkan ke rekapitulasi
  alert(`Data berhasil disubmit! Durasi: ${durationInSeconds} detik.`);
  router.push('/rekapitulasi');
}

// PERUBAHAN: Fungsi ketika user mengklik 'TIDAK'
function cancelSubmit() {
  showSubmitDialog.value = false; // Tutup dialog
  // Tidak ada perubahan navigasi, user tetap di halaman wawancara
}

function handleSubmit() {
  // Fungsi ini sekarang tidak langsung submit, melainkan membuka dialog
  // Ini tetap dipertahankan karena ada @submit.prevent="handleSubmit" di form
  // Namun, logikanya dipindahkan ke confirmSubmit()
  openSubmitDialog();
}

function handleClear() {
  if (confirm('Yakin ingin menghapus semua data?')) {
    for (const key in manualForm.value) {
      manualForm.value[key] = "";
    }
  }
}
</script>

<style scoped>
/* Semua style dari Kode B2 dipertahankan */
.back-btn {
  align-self: flex-start;
  margin-bottom: 20px;
  background-color: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}
.back-btn:hover {
  background-color: #0056b3;
}

.interview-page {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  background: #ffffff;
  min-height: 100vh;
  box-sizing: border-box;
  position: relative;
  padding-bottom: 120px;
  display: flex;
  flex-direction: column;
}

.form-title {
  text-align: center;
  color: #1155cc;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 30px;
  margin-top: 0;
}

.interview-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.question-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-input {
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  background: #f5f5f5;
  font-size: 14px;
  outline: none;
  transition: background-color 0.2s;
}

.form-input:focus {
  background: #eeeeee;
}

.bottom-action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: #ffffff;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 60px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.action-btn {
  padding: 12px 32px;
  border: none;
  border-radius: 25px;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  min-width: 120px;
  transition: all 0.2s;
}

.clear-btn {
  background: #dc3545;
  color: white;
}

.clear-btn:hover {
  background: #c82333;
}

.submit-btn {
  background: #007bff;
  color: white;
}

.submit-btn:hover {
  background: #0056b3;
}

.duration-display {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  min-width: 60px;
  text-align: center;
}

@media (max-width: 480px) {
  .interview-page {
    max-width: 100vw;
    padding: 16px;
    padding-bottom: 120px;
  }

  .form-title {
    font-size: 16px;
    margin-bottom: 25px;
  }

  .bottom-action-bar {
    gap: 40px;
    padding: 16px;
  }

  .action-btn {
    min-width: 100px;
    padding: 10px 24px;
    font-size: 11px;
  }
}

@media (max-width: 768px) and (orientation: landscape) {
  .interview-page {
    padding-bottom: 100px;
  }

  .bottom-action-bar {
    padding: 12px 20px;
  }
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.dialog-box {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  text-align: center;
  max-width: 350px;
  width: 90%;
}

.dialog-box p {
  font-size: 1.1rem;
  margin-bottom: 25px;
  color: #333;
}

.dialog-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.dialog-btn {
  padding: 12px 25px;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.dialog-btn:hover {
  transform: translateY(-2px);
}

.confirm-btn {
  background-color: #28a745;
  color: white;
}

.confirm-btn:hover {
  background-color: #218838;
}

.cancel-btn {
  background-color: #dc3545;
  color: white;
}

.cancel-btn:hover {
  background-color: #c82333;
}
</style>
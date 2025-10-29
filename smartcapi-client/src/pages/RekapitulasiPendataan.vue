<template>
  <div class="page-container">
    <div class="header">
      <h1 class="title">Rekapitulasi Pendataan</h1>
      <div class="header-actions">
        <button class="add-btn" @click="goToInterview">
          <span>+</span> Tambah Data Wawancara
        </button>
        
        <div class="profile-section" @click="goToProfile" title="Lihat Profil">
          <button class="profile-icon-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.96C6.04 14.03 10 12.9 12 12.9C13.99 12.9 17.96 14.03 18 15.96C16.71 17.92 14.5 19.2 12 19.2Z"/>
            </svg>
          </button>
          <span class="profile-name">{{ authStore.userName.value }}</span>
        </div>
        </div>
    </div>

    <div class="tabs-container">
      <button
        :class="['tab-btn', { active: activeTab === 'ai' }]"
        @click="activeTab = 'ai'">
        Mode AI
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'manual' }]"
        @click="activeTab = 'manual'">
        Mode Manual
      </button>
    </div>

    <div v-if="activeTab === 'ai'">
      <RekapitulasiTabelAI
        :data="aiData"
        :getStatusClass="getStatusClass"
        :playRecording="playRecording"
        :handleEdit="handleEdit"
        :handleDelete="handleDelete"
      />
    </div>
    <div v-else-if="activeTab === 'manual'">
      <RekapitulasiTabelManual
        :data="manualData"
        :getStatusClass="getStatusClass"
        :handleEdit="handleEdit"
        :handleDelete="handleDelete"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import RekapitulasiTabelAI from '../components/Rekapitulasi/RekapitulasiTabelAI.vue';
import RekapitulasiTabelManual from '../components/Rekapitulasi/RekapitulasiTabelManual.vue';
import { useAuthStore } from '../store/auth';
import { useInterviewStore } from '../store/interview';

const router = useRouter();
const authStore = useAuthStore();
const interviewStore = useInterviewStore(); // Get the interview store
const interviewData = ref([]);
const currentlyPlaying = ref(null);
const activeTab = ref('ai');

const API_BASE_URL = 'http://127.0.0.1:8000/api'; // Point to the new FastAPI backend

const aiData = computed(() => {
  return interviewData.value.filter(item => item.mode === 'dengan Asistensi AI');
});

const manualData = computed(() => {
  return interviewData.value.filter(item => item.mode === 'tanpa Asistensi AI');
});

async function fetchInterviews() {
  if (!authStore.isAuthenticated.value) {
    alert('Anda harus login untuk melihat rekapitulasi.');
    router.push('/login');
    return;
  }
  try {
    // Fetch all interviews from the new backend
    const response = await axios.get(`${API_BASE_URL}/interviews`, {
      headers: {
        // Assuming the new backend uses the same token mechanism
        'Authorization': `Bearer ${authStore.userToken.value}`
      }
    });
    interviewData.value = response.data;
  } catch (error) {
    console.error("Gagal mengambil data rekapitulasi:", error);
    alert("Gagal memuat data rekapitulasi.");
    if (error.response && error.response.status === 401) {
      authStore.logout();
      router.push('/login');
    }
  }
}

onMounted(() => {
  if (!authStore.isAuthenticated.value) {
    router.push('/login');
  } else {
    fetchInterviews();
  }
});

function playRecording(item) {
  if (!item.has_recording || !item.recording_path) {
    alert("Responden ini tidak memiliki data rekaman.");
    return;
  }
  if (currentlyPlaying.value) {
    currentlyPlaying.value.pause();
  }
  const audioUrl = `${API_BASE_URL}${item.recording_path}`;
  const audio = new Audio(audioUrl);
  currentlyPlaying.value = audio;
  audio.play().catch(e => {
    console.error("Gagal memutar audio:", e);
    alert("Tidak dapat memutar file audio.");
  });
}

function getStatusClass(status) {
  if (status === 'Submitted') return 'status-badge status-submitted';
  if (status === 'Pending') return 'status-badge status-pending';
  return 'status-badge status-no-data';
}

function handleEdit(item) {
  alert(`Fungsi edit untuk "${item.name}" belum diimplementasikan.`);
}

async function handleDelete(item) {
  if (confirm(`Yakin ingin menghapus data responden "${item.name}"?`)) {
    try {
      await axios.delete(`${API_BASE_URL}interviews.php?id=${item.id}`);
      alert('Data berhasil dihapus.');
      fetchInterviews();
    } catch (error) {
      console.error("Gagal menghapus data:", error);
      alert("Gagal menghapus data.");
    }
  }
}

function goToInterview() {
  if (!authStore.isAuthenticated.value) {
    alert('Anda harus login untuk menambah data.');
    router.push('/login');
    return;
  }
  router.push('/select-mode');
}

function goToProfile() {
  if (!authStore.isAuthenticated.value) {
    alert('Anda harus login untuk melihat profil.');
    router.push('/login');
    return;
  }
  router.push('/profile');
}
</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* PERUBAHAN STYLE DIMULAI DI SINI */
.profile-section {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 20px;
  transition: background-color 0.2s;
}
.profile-section:hover {
  background-color: #f0f0f0;
}
.profile-name {
  font-weight: 600;
  color: #333;
  font-size: 15px;
}
.profile-icon-btn {
  /* Dihapus: cursor: pointer, karena sudah ada di wrapper */
  background: none;
  border: none;
  color: #1976d2;
  padding: 5px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}
/* AKHIR DARI PERUBAHAN STYLE */

.profile-icon-btn:hover {
  /* Dihapus: background-color dan transform, agar efek hover menyatu di wrapper */
}

.profile-icon-btn svg {
  width: 28px;
  height: 28px;
}
.page-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 1rem;
}
.title {
  color: #1976d2;
  font-size: 1.8rem;
}
.add-btn {
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
}
.add-btn:hover {
  background-color: #218838;
}
.add-btn span {
  font-size: 20px;
  line-height: 1;
}

.tabs-container {
  display: flex;
  gap: 10px;
  margin-bottom: 2rem;
  border-bottom: 1px solid #ddd;
}
.tab-btn {
  padding: 10px 20px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  background-color: transparent;
  cursor: pointer;
  color: #888;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease-in-out;
}
.tab-btn:hover {
  color: #333;
}
.tab-btn.active {
  color: #1976d2;
  border-bottom-color: #1976d2;
}
</style>
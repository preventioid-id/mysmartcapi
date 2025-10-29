<template>
  <div class="profile-page-container">
    <button class="back-btn" @click="goBack">&lt;&lt; Kembali</button>

    <div class="profile-card">
      <div class="profile-header">
        <h1 class="profile-title">Profil Pengguna</h1>
        <div class="profile-avatar">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5.52 19c.64-2.2 1.84-3 3.22-3h6.52c1.38 0 2.58.8 3.22 3"/>
            <circle cx="12" cy="10" r="3"/>
            <circle cx="12" cy="12" r="10"/>
          </svg>
        </div>
        <h2 class="user-name">{{ userProfile.full_name || 'Memuat...' }}</h2>
        <p class="user-email">{{ userProfile.email || 'Memuat...' }}</p>
      </div>

      <div class="profile-details">
        <h3>Detail Informasi</h3>
        <div class="detail-item">
          <strong>ID Pengguna:</strong> <span>{{ authStore.userId || 'N/A' }}</span>
        </div>
        <div class="detail-item">
          <strong>Username:</strong> <span>{{ userProfile.username || 'Memuat...' }}</span>
        </div>
        <div class="detail-item">
          <strong>Nomor Telepon:</strong> <span>{{ userProfile.phone || 'Memuat...' }}</span>
        </div>
        <div class="detail-item">
          <strong>Tanggal Daftar:</strong> <span>{{ userProfile.registered_at || 'Memuat...' }}</span>
        </div>
        <div class="detail-item">
          <strong>Status Suara:</strong>
          <span :class="{'status-voice-recorded': userProfile.has_voice_registered, 'status-voice-pending': !userProfile.has_voice_registered}">
            {{ userProfile.has_voice_registered ? 'Terdaftar' : 'Belum Terdaftar' }}
          </span>
        </div>
        </div>

      <button class="logout-btn" @click="handleLogout">LOGOUT</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { useAuthStore } from '../store/auth';

const router = useRouter();
const authStore = useAuthStore();
const userProfile = ref({
  // PERUBAHAN: Menyesuaikan state dengan data dari registrasi
  full_name: '', // Mengganti 'name' menjadi 'full_name' agar konsisten
  username: '',
  email: '',
  phone: '',
  registered_at: '',
  has_voice_registered: false,
});

const API_BASE_URL = 'http://localhost/smartcapi_pwa/api/';

const fetchUserProfile = async () => {
  if (!authStore.isAuthenticated.value || !authStore.userId.value) {
    alert('Anda harus login untuk melihat profil.');
    router.push('/login');
    return;
  }

  try {
    const response = await axios.get(`${API_BASE_URL}user_profile.php?id=${authStore.userId.value}`, {
      headers: {
        'Authorization': `Bearer ${authStore.userToken.value}`
      }
    });

    if (response.data && response.data.success) {
      userProfile.value = response.data.data;
    } else {
      console.error("Gagal mengambil data profil:", response.data.message);
      alert("Gagal memuat detail profil. Silakan coba lagi.");
    }
  } catch (error) {
    console.error("Error fetching user profile:", error);
    alert("Terjadi kesalahan saat memuat profil. Silakan coba lagi.");
    authStore.logout();
    router.push('/login');
  }
};

const handleLogout = () => {
  if (confirm('Anda yakin ingin logout?')) {
    authStore.logout();
    router.push('/login');
  }
};

function goBack() {
  router.go(-1);
}

onMounted(() => {
  if (authStore.isAuthenticated.value) {
    fetchUserProfile();
  } else {
    alert('Anda harus login untuk melihat profil.');
    router.push('/login');
  }
});
</script>

<style scoped>
.profile-page-container {
  max-width: 600px;
  margin: 2rem auto;
  padding: 20px;
  background-color: #f7f9fc;
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.back-btn {
  align-self: flex-start;
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}
.back-btn:hover {
  background-color: #5a6268;
}

.profile-card {
  background-color: #ffffff;
  border-radius: 10px;
  padding: 30px;
  text-align: center;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
}

.profile-header {
  margin-bottom: 25px;
}

.profile-title {
  color: #1976d2;
  font-size: 2rem;
  margin-bottom: 15px;
}

.profile-avatar {
  width: 100px;
  height: 100px;
  background-color: #e0e0e0;
  border-radius: 50%;
  margin: 0 auto 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #757575;
  border: 3px solid #1976d2;
}

.profile-avatar svg {
  width: 60px;
  height: 60px;
  color: #1976d2;
}

.user-name {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 5px;
}

.user-email {
  font-size: 1.1rem;
  color: #777;
}

.profile-details {
  text-align: left;
  margin-bottom: 30px;
  border-top: 1px solid #eee;
  padding-top: 25px;
}

.profile-details h3 {
  color: #1976d2;
  font-size: 1.5rem;
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed #f0f0f0;
  font-size: 1.05rem;
  color: #555;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item strong {
  color: #333;
  min-width: 150px;
}

.status-voice-recorded {
  color: #28a745; /* Hijau */
  font-weight: bold;
}

.status-voice-pending {
  color: #ffc107; /* Kuning/Oranye */
  font-weight: bold;
}

.logout-btn {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 12px 25px;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  width: 100%;
}
.logout-btn:hover {
  background-color: #c82333;
  transform: translateY(-2px);
}
</style>
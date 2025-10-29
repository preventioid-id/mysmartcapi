<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-title">Registrasi Akun</div>
      <form @submit.prevent="onRegister" class="register-form">
        <div class="form-group">
          <label>Nama Lengkap</label>
          <input 
            v-model="full_name" 
            type="text"
            placeholder="Nama Lengkap" 
            required 
          />
        </div>
        
        <div class="form-group">
          <label>Username</label>
          <input 
            v-model="username" 
            type="text"
            placeholder="Username" 
            required 
          />
        </div>
        
        <div class="form-group">
          <label>Password</label>
          <input 
            v-model="password" 
            type="password" 
            placeholder="Password" 
            required 
          />
        </div>
        
        <div class="form-group">
          <label>Konfirmasi Password</label>
          <input 
            v-model="retype" 
            type="password" 
            placeholder="Konfirmasi Password" 
            required 
          />
        </div>
        
        <div class="form-group">
          <label>Email</label>
          <input 
            v-model="email" 
            type="email" 
            placeholder="Email" 
            required 
          />
        </div>
        
        <div class="form-group">
          <label>Nomor Telepon</label>
          <input 
            v-model="phone" 
            type="tel"
            placeholder="Nomor Telepon" 
            required 
          />
        </div>
        
        <div v-if="error" class="error-message">{{ error }}</div>
        
        <button type="submit" class="btn-next" :disabled="loading">
          {{ loading ? 'Memproses...' : 'Lanjutkan ke Rekam Suara' }}
        </button>
      </form>
      <div class="back-link">
        <a href="#" @click.prevent="goBackToLogin">Sudah punya akun? Login di sini</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../store/user';
import { api } from '../services/api'; // 1. Impor service api

const router = useRouter();
const userStore = useUserStore();

// State untuk form
const full_name = ref('');
const username = ref('');
const password = ref('');
const retype = ref('');
const email = ref('');
const phone = ref('');
const loading = ref(false);
const error = ref('');

async function onRegister() {
  error.value = '';
  if (password.value !== retype.value) {
    error.value = "Password dan konfirmasi password tidak cocok!";
    return;
  }
  loading.value = true;
  try {
    // 2. Siapkan data untuk dikirim ke backend
    const userData = {
      full_name: full_name.value,
      username: username.value,
      password: password.value,
      email: email.value,
      phone: phone.value,
    };

    // 3. Panggil API registrasi
    const response = await api.register(userData);
    console.log('Registrasi berhasil:', response.data);

    // Simpan nama lengkap ke store (opsional, bisa juga ambil dari response)
    userStore.setRegistrationData({ fullName: full_name.value });
    
    // Arahkan ke halaman rekam suara
    router.push('/register-voice');

  } catch(e) {
    // 4. Tangani error dari backend
    if (e.response && e.response.data && e.response.data.detail) {
      error.value = e.response.data.detail;
    } else {
      error.value = e.message || "Registrasi gagal. Silakan coba lagi.";
    }
  } finally {
    loading.value = false;
  }
}

function goBackToLogin() {
  router.push('/');
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.register-container {
  background: white;
  border-radius: 8px;
  padding: 30px 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}
.register-title {
  color: #1976d2;
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 30px;
}
.register-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-group label {
  color: #333;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 4px;
}
.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: #f0f0f0;
  border-radius: 6px;
  font-size: 1rem;
  color: #333;
  box-sizing: border-box;
  transition: background-color 0.2s;
}
.form-group input:focus {
  outline: none;
  background: #e8e8e8;
}
.error-message {
  color: #e11d48;
  font-size: 0.9rem;
  text-align: center;
  margin-top: 10px;
}
.btn-next {
  width: 100%;
  padding: 12px 20px;
  border: none;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
  background: #1976d2;
  color: white;
  margin-top: 20px;
}
.btn-next:hover:not(:disabled) {
  background: #1565c0;
}
.btn-next:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.back-link {
  margin-top: 1.5rem;
  text-align: center;
}
.back-link a {
  color: #007bff;
  text-decoration: none;
  font-weight: bold;
  font-size: 0.9em;
}
</style>
<template>
  <div class="login-page">
    <div class="login-logo">
      <img src="@/assets/smartcapi-logo.png" alt="SmartCAPI Logo" class="logo-img" />
      <span class="logo-text">Smart Computer Assisted Personal Interviewing</span>
    </div>
    <div class="login-card">
      <form @submit.prevent="onLogin">
        <input v-model="username" type="text" placeholder="Username" required />
        <input v-model="password" type="password" placeholder="Password" required />
        <button type="submit" class="login-btn">Log in</button>
      </form>
      <div class="login-links">
        <span>Belum punya akun? Klik <a href="#" @click.prevent="goRegister">daftar</a></span>
        <span>Lupa password ? Klik <a href="#" @click.prevent="goForgot">sini</a></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
// 1. Impor auth store yang sudah Anda buat
import { useAuthStore } from '../store/auth';

const router = useRouter();
// 2. Inisialisasi store agar bisa digunakan
const authStore = useAuthStore(); 
const username = ref('');
const password = ref('');

function onLogin() {
  console.log('Attempting login...');
  
  // 3. Panggil aksi login dari authStore sebelum navigasi
  // Di aplikasi nyata, ID, nama, dan token akan didapat dari respons API.
  // Untuk contoh ini, kita gunakan data dummy.
  authStore.login('user-001', username.value, 'dummy-secret-token-from-api');

  // 4. Arahkan ke halaman rekapitulasi SETELAH status login diubah
  router.push('/rekapitulasi');
}

function goRegister() {
  router.push('/register');
}

function goForgot() {
  router.push('/forget-password');
}
</script>

<style scoped>
/* Style tidak berubah */
.login-page {
  min-height: 100vh;
  background: #f6f8fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.login-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
  width: 100%;
  max-width: 400px;
}
.logo-img {
  width: 100%;
  margin-bottom: 16px;
}
.logo-text {
  font-size: 1.1rem;
  font-weight: bold;
  color: #222;
  font-family: 'Montserrat', Arial, Helvetica, sans-serif;
  text-align: center;
  line-height: 1.4;
}
.login-card {
  background: #ededed;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(48,52,54,0.04);
  padding: 2rem 2.3rem 1.3rem 2.3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 400px;
  box-sizing: border-box;
}
.login-card form {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 13px;
}
.login-card input[type="text"],
.login-card input[type="password"] {
  width: 100%;
  border: 1px solid #b7b7b7;
  border-radius: 5px;
  padding: 0.7em 1em;
  font-size: 1rem;
}
.login-btn {
  background: #2196f3;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.7em 0;
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
  transition: filter 0.2s;
}
.login-btn:hover { filter: brightness(0.95); }
.login-links {
  margin-top: 8px;
  font-size: 0.98em;
  color: #222;
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}
.login-links a {
  color: #1565c0;
  text-decoration: underline;
  cursor: pointer;
  font-weight: bold;
}
</style>
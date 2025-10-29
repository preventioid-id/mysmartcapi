<template>
  <div class="forget-password-page">
    <div class="card">
      <h2>Lupa Password</h2>
      <p class="subtitle">
        Masukkan alamat email Anda yang terdaftar untuk melanjutkan.
      </p>
      <form @submit.prevent="handleSubmit">
        <input 
          v-model="email" 
          type="email" 
          placeholder="Alamat Email Anda" 
          required 
        />
        <button type="submit" class="submit-btn">
          Lanjutkan
        </button>
      </form>
      <div class="back-link">
        <a href="#" @click.prevent="goBackToLogin">Kembali ke Halaman Login</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const email = ref('');
const router = useRouter();

function handleSubmit() {
  if (!email.value) {
    alert('Mohon masukkan alamat email Anda.');
    return;
  }
  // Arahkan ke halaman reset password dengan email sebagai query parameter
  router.push({ path: '/reset-password', query: { email: email.value } });
}

function goBackToLogin() {
  router.push('/');
}
</script>

<style scoped>
/* Style tidak ada yang diubah, namun ditambahkan selector untuk state disabled */
.forget-password-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  padding: 20px;
  background-color: #f6f8fa;
}
.card {
  background: #fff;
  padding: 2.5rem 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 450px;
  text-align: center;
}
h2 {
  margin-bottom: 1rem;
  font-size: 1.8rem;
  color: #333;
}
.subtitle {
  margin-bottom: 2rem;
  color: #666;
  line-height: 1.5;
}
form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
input[type="email"] {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0.8em 1em;
  font-size: 1rem;
}
.submit-btn {
  background: #28a745;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.8em 0;
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
  transition: background-color 0.2s;
}
.submit-btn:hover {
  background-color: #218838;
}
/* BARU: Style untuk tombol saat disabled */
.submit-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}
.back-link {
  margin-top: 1.5rem;
  font-size: 0.9em;
}
.back-link a {
  color: #007bff;
  text-decoration: none;
  font-weight: bold;
}
</style>
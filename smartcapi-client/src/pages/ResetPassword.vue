
<template>
  <div class="reset-password-page">
    <div class="card">
      <h2>Reset Password Anda</h2>
      <p class="subtitle">
        Masukkan email terdaftar Anda dan password baru.
      </p>
      <div v-if="email" class="email-display">
        <p>Mereset password untuk akun:</p>
        <strong>{{ email }}</strong>
      </div>
      <p v-else class="subtitle">
        Memuat informasi akun...
      </p>
      <form @submit.prevent="handleSubmit">
        <input 
          v-model="newPassword" 
          type="password" 
          placeholder="Password Baru" 
          required 
          :disabled="isLoading"
        />
        <input 
          v-model="confirmPassword" 
          type="password" 
          placeholder="Konfirmasi Password Baru" 
          required 
          :disabled="isLoading"
        />
        <button type="submit" class="submit-btn" :disabled="isLoading || !email">
          {{ isLoading ? 'Mereset...' : 'Reset Password' }}
        </button>
      </form>
      <div v-if="message" :class="{ 'message-success': isSuccess, 'message-error': !isSuccess }">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const email = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const message = ref('');
const isSuccess = ref(false);

// Ambil email dari query parameter saat komponen dimuat
onMounted(() => {
  if (route.query.email) {
    email.value = route.query.email;
  } else {
    // Jika tidak ada email di URL, beri pesan error dan mungkin arahkan kembali
    isSuccess.value = false;
    message.value = "Email tidak ditemukan. Silakan ulangi proses dari halaman Lupa Password.";
  }
});

async function handleSubmit() {
  message.value = '';
  if (newPassword.value !== confirmPassword.value) {
    isSuccess.value = false;
    message.value = 'Password dan konfirmasi password tidak cocok.';
    return;
  }

  if (!email.value || !newPassword.value) {
    isSuccess.value = false;
    message.value = 'Email dan password baru tidak boleh kosong.';
    return;
  }

  isLoading.value = true;

  try {
    const response = await fetch('http://localhost:8000/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value,
        new_password: newPassword.value,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || 'Gagal mereset password.');
    }

    isSuccess.value = true;
    message.value = result.message + " Anda akan diarahkan ke halaman login.";

    // Arahkan ke halaman login setelah beberapa detik
    setTimeout(() => {
      router.push('/');
    }, 3000);

  } catch (error) {
    isSuccess.value = false;
    message.value = `Terjadi kesalahan: ${error.message}`;
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.email-display {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f0f4f8;
  border-radius: 8px;
  color: #333;
}

.email-display p {
  margin: 0;
  font-size: 0.9rem;
}

.email-display strong {
  font-size: 1.1rem;
  color: #0056b3;
}

/* Menggunakan style yang mirip dengan ForgetPassword.vue untuk konsistensi */
.reset-password-page {
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
input {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0.8em 1em;
  font-size: 1rem;
}
.submit-btn {
  background: #007bff;
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
  background-color: #0056b3;
}
.submit-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}
.message-success {
  margin-top: 1rem;
  color: #28a745;
  font-weight: bold;
}
.message-error {
  margin-top: 1rem;
  color: #dc3545;
  font-weight: bold;
}
</style>

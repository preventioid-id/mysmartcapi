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
        <span>Mau Tahu tentang SmartCAPI ? Klik <a href="#" @click.prevent="goAboutUs">sini</a></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
// Pastikan path store sesuai struktur proyek Anda.
// Jika store berada di src/store/auth.ts atau .js, gunakan '@/store/auth'.
// Jika file ini ada di folder pages dan store di src/store, '../store/auth' juga bisa.
// Silakan sesuaikan path jika Anda mendapat error "module not found".
import { useAuthStore } from '@/store/auth' // ganti ke '../store/auth' bila diperlukan

const router = useRouter()
const authStore = (typeof useAuthStore === 'function') ? useAuthStore() : null

const username = ref('')
const password = ref('')

/**
 * Helper check for admin credentials as requested:
 * username: admincapi
 * password: supercapi
 */
const isAdminCredential = (u, p) => u === 'admincapi' && p === 'supercapi'

async function onLogin() {
  // Validasi singkat
  if (!username.value || !password.value) {
    alert('Masukkan username dan password')
    return
  }

  try {
    // Jika ada authStore dengan method login, panggil. Asumsikan signature login(username, password).
    if (authStore && typeof authStore.login === 'function') {
      // Jika implementasi login pada store mengembalikan promise/result, tunggu hasilnya.
      const res = await authStore.login(username.value, password.value)
      // Tanggapan login bisa bervariasi; kita tangani beberapa kemungkinan umum
      if (res === true || (res && res.ok) || (res && res.user)) {
        // Jika kredensial yang dimasukkan merupakan admin khusus, arahkan ke RekapitulasiUser.vue
        if (isAdminCredential(username.value, password.value)) {
          // Jika store menyediakan setter untuk user, cobalah set role admin agar konsisten
          try {
            if (authStore && typeof authStore.setUser === 'function') {
              authStore.setUser({
                username: 'admincapi',
                role: 'admin',
                name: 'Administrator SmartCAPI',
                token: (res && res.token) ? res.token : 'admin-token-please-replace'
              })
            } else if (res && res.user) {
              // jika response sudah berisi user, coba pastikan role ada
              res.user.role = res.user.role || 'admin'
              localStorage.setItem('auth_user', JSON.stringify(res.user))
            } else {
              // fallback: simpan user admin ke localStorage agar route guard membaca role
              const adminUser = { username: 'admincapi', role: 'admin', token: (res && res.token) ? res.token : 'admin-token-please-replace' }
              localStorage.setItem('auth_user', JSON.stringify(adminUser))
              localStorage.setItem('auth_token', adminUser.token)
            }
          } catch (e) {
            // jangan ganggu alur bila store tidak mendukung setUser
            console.warn('Could not set user in store', e)
          }

          router.push('/rekapitulasi-user')
          return
        }

        // Keberhasilan: arahkan pengguna (non-admin)
        router.push('/rekapitulasi')
        return
      } else {
        // Jika login gagal, tampilkan pesan bila ada
        const msg = (res && res.error) ? res.error : 'Login gagal. Periksa kredensial.'
        alert(msg)
        return
      }
    }

    // Jika tidak ada authStore (fallback/testing), simulasikan login sederhana
    // Pada fallback ini, kita simpan user dasar di localStorage agar route-guard dapat membaca role
    const fallbackUser = {
      username: username.value,
      role: username.value === 'admincapi' && password.value === 'supercapi' ? 'admin' : 'user',
      token: 'local-fallback-token'
    }
    localStorage.setItem('auth_user', JSON.stringify(fallbackUser))
    localStorage.setItem('auth_token', fallbackUser.token)

    // tambahan: jika kredensial admin, arahkan ke halaman rekapitulasi user admin
    if (isAdminCredential(username.value, password.value)) {
      router.push('/rekapitulasi-user')
      return
    }

    router.push('/rekapitulasi')
  } catch (err) {
    console.error('Login error', err)
    alert('Terjadi kesalahan saat proses login.')
  }
}

function goRegister() {
  router.push('/register')
}

function goForgot() {
  router.push('/forget-password')
}

function goAboutUs() {
  router.push('/about-us')
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
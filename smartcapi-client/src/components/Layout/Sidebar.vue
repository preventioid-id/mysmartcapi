<template>
  <aside class="sidebar">
    <template v-if="!isLoginPage">
      <ul>
        <li><router-link to="/">Beranda</router-link></li>
        <li><router-link to="/settings">Pengaturan</router-link></li>
        <li><router-link to="/manual">Isi Data Manual</router-link></li>
      </ul>
    </template>
    <template v-else>
      <div class="login-form">
        <input v-model="username" class="login-input" placeholder="Username" />
        <input v-model="password" class="login-input" placeholder="Password" type="password" />
        <!-- ... -->
      </div>
    </template>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const isLoginPage = computed(() => route.name === 'Login')

// Hanya digunakan pada login page
const username = ref('')
const password = ref('')
</script>

<style scoped>
.sidebar {
  min-width: 180px;
  background: #f0f4f8;
  height: 100vh;
  padding: 1.2em 0.6em;
}
.sidebar ul {
  list-style: none;
  padding: 0;
}
.sidebar li {
  margin: 1em 0;
}
.sidebar a.router-link-active {
  color: #1565c0;
  font-weight: bold;
}

/* Style login form jika tampil di sidebar */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-top: 2em;
}
.login-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.7em 1em;
  font-size: 1rem;
  border: 1px solid #b7b7b7;
  border-radius: 5px;
  margin-bottom: 10px;
  background: #fff;
}
</style>
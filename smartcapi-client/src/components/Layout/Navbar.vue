<template>
  <nav class="navbar">
    <div class="nav-left">
      <span class="logo">smartcapi</span>
    </div>
    <div class="nav-right">
      <span v-if="user">{{ user.nama }}</span>
      <Button v-if="user" @click="logout" type="danger" icon="fa fa-sign-out-alt">Logout</Button>
    </div>
  </nav>
</template>

<script setup>
import Button from '../ui/Button.vue'
import { useUserStore } from '../../store/user'
const userStore = useUserStore()
const user = userStore.user

function logout() {
  userStore.logout()
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1565c0;
  color: #fff;
  padding: 0.7em 1.4em;
}
.logo {
  font-weight: bold;
  font-size: 1.2em;
  letter-spacing: 1px;
}
.nav-right {
  display: flex;
  align-items: center;
  gap: 0.7em;
}
</style>
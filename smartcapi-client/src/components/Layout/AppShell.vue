<template>
  <div class="app-shell">
    <Navbar />
    <div class="main-area">
      <Sidebar v-if="showSidebar" />
      <PageWrapper>
        <slot />
      </PageWrapper>
    </div>
    <NotificationBar />
  </div>
</template>

<script setup>
import Navbar from './Navbar.vue'
import Sidebar from './Sidebar.vue'
import PageWrapper from './PageWrapper.vue'
import NotificationBar from './NotificationBar.vue'

// Bisa pakai state global untuk atur visibilitas sidebar
const showSidebar = true
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: #f3f6fa;
}
.main-area {
  display: flex;
  gap: 1em;
}
</style>
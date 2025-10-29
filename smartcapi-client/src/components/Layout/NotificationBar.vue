<template>
  <div v-if="notification" class="notification-bar" :class="notification.type">
    {{ notification.message }}
    <span class="close" @click="clear">×</span>
  </div>
</template>

<script setup>
import { useNotificationStore } from '../../store/notification'
const notificationStore = useNotificationStore()
const notification = notificationStore.current

function clear() {
  notificationStore.clear()
}
</script>

<style scoped>
.notification-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: #1565c0;
  color: #fff;
  padding: 1em 2em;
  z-index: 99;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.notification-bar.success { background: #43a047; }
.notification-bar.danger { background: #e53935; }
.close { cursor: pointer; font-weight: bold; margin-left: 2em; }
</style>
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  const current = ref(null)
  function notify(message, type = 'success') {
    current.value = { message, type }
    setTimeout(() => current.value = null, 4500)
  }
  function clear() { current.value = null }
  return { current, notify, clear }
})
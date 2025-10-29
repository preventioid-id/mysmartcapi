import { ref } from 'vue'
const mode = ref(null)
export function useMode() {
  function setMode(m) { mode.value = m }
  function getMode() { return mode.value }
  return { mode, setMode, getMode }
}
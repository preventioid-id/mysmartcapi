import { ref } from 'vue'
import { sendAudioToBackend } from '../services/api'
const recording = ref(false)
let mediaRecorder, chunks = []
async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  mediaRecorder = new MediaRecorder(stream)
  mediaRecorder.start()
  recording.value = true
  mediaRecorder.ondataavailable = e => chunks.push(e.data)
}
async function stopRecording() {
  mediaRecorder.stop()
  recording.value = false
  mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, { type: 'audio/webm' })
    await sendAudioToBackend(blob)
    chunks = []
  }
}
export function useAudioRecorder() { return { recording, startRecording, stopRecording } }
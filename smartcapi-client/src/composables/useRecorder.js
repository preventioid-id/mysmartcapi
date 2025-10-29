import { ref } from 'vue';

export function useRecorder(onDataAvailable) {
  const isRecording = ref(false);
  const mediaRecorder = ref(null);

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    mediaRecorder.value.ondataavailable = e => {
      if (e.data.size > 0) onDataAvailable(e.data);
    };
    mediaRecorder.value.start(500); // Kirim chunk setiap 500ms
    isRecording.value = true;
  }

  function stopRecording() {
    mediaRecorder.value?.stop();
    isRecording.value = false;
  }

  return { isRecording, startRecording, stopRecording };
}
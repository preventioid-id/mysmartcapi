<template>
  <div>
    <Button @click="startRecording" :disabled="recording">Mulai Rekam</Button>
    <Button @click="stopRecording" :disabled="!recording">Stop Rekam</Button>
    <div v-if="audioUrl">
      <audio :src="audioUrl" controls />
    </div>
  </div>
</template>
<script setup>
import Button from '../ui/Button.vue'
import { useAudioRecorderStore } from '../../store/audioRecorder'

const audioRecorder = useAudioRecorderStore()
const { recording, audioUrl } = audioRecorder

function startRecording() { audioRecorder.start() }
function stopRecording() { audioRecorder.stop() }
</script>
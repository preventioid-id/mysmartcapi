<template>
  <div>
    <Button :type="isRecording ? 'danger' : 'primary'" @click="toggle">
      {{ isRecording ? 'Stop Recording' : 'Start Recording' }}
    </Button>
  </div>
</template>

<script setup>
import { useInterviewStore } from '../../store/interview'
import Button from '../ui/Button.vue'

const interviewStore = useInterviewStore()
const { isRecording } = interviewStore

function toggle() {
  if (isRecording) interviewStore.stopInterview()
  else interviewStore.startInterview()
}
</script>
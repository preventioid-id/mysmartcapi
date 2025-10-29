<template>
  <div class="select-mode">
    <div class="logo-container">
      <img src="@/assets/smartcapi-logo.png" alt="SmartCAPI Logo" class="logo-img" />
    </div>
    <h2>Pilih Mode Pendataan</h2>
    <div class="button-container">
      <Button @click="choose('ai')">SmartCAPI dengan AI (Rekam Suara)</Button>
      <Button @click="choose('manual')">SmartCAPI Manual (Input Keyboard)</Button>
    </div>
  </div>
</template>

<script setup>
import Button from '../components/ui/Button.vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../store/user';
// 1. Impor store interview
import { useInterviewStore } from '../store/interview';

const router = useRouter();
const userStore = useUserStore();
// 2. Inisialisasi store interview
const interviewStore = useInterviewStore();

function choose(mode) {
  userStore.setInterviewMode(mode);

  interviewStore.startInterviewTimer();

  if (mode === 'ai') {
    // Jika mode adalah 'ai', akan diarahkan ke /interview
    router.push('/interview'); 
  } else {
    // Jika mode bukan 'ai' (yaitu 'manual'), akan diarahkan ke /interview-manual
    router.push('/interview-manual');
  }
}
</script>

<style scoped>
/* Style tidak perlu diubah */
.select-mode { 
  text-align: center; 
  margin-top: 2em;
  padding: 20px;
}
.logo-container {
  width: 100%;
  max-width: 400px;
  margin: 0 auto 2.5em auto;
}
.logo-img {
  width: 100%;
}
h2 {
  margin-bottom: 2em;
}
.button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}
</style>
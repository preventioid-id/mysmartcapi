import { ref } from 'vue';
import { defineStore } from 'pinia';
// import axios from 'axios'; // Aktifkan jika Anda menggunakan axios untuk API calls

export const useUserStore = defineStore('user', () => {
  // === STATE ===
  // State untuk pengguna yang sedang login
  const user = ref(JSON.parse(localStorage.getItem('user')) || null);
  const token = ref(localStorage.getItem('token') || '');

  // State untuk data registrasi sementara
  const registrationData = ref({
    fullName: '',
  });
  
  // State untuk mode wawancara (digabungkan dari Kode 1)
  const interviewMode = ref(localStorage.getItem('interviewMode') || 'ai');


  // === ACTIONS ===
  // Aksi login dan logout
  async function login(username, password) {
    console.log("Login action called with:", username);
    // Logika API call Anda akan ada di sini
  }

  function logout() {
    token.value = '';
    user.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  // Aksi untuk proses registrasi
  function setRegistrationData(data) {
    registrationData.value.fullName = data.fullName;
    localStorage.setItem('registrationFullName', data.fullName);
  }

  function clearRegistrationData() {
    registrationData.value.fullName = '';
    localStorage.removeItem('registrationFullName');
  }
  
  function loadRegistrationData() {
      const storedName = localStorage.getItem('registrationFullName');
      if (storedName) {
          registrationData.value.fullName = storedName;
      }
  }

  // Aksi untuk mengatur mode wawancara (digabungkan dari Kode 1)
  function setInterviewMode(mode) {
    interviewMode.value = mode;
    localStorage.setItem('interviewMode', mode);
  }

  // Kembalikan semua state dan actions agar bisa digunakan
  return {
    user,
    token,
    registrationData,
    interviewMode, // Ditambahkan
    login,
    logout,
    setRegistrationData,
    clearRegistrationData,
    loadRegistrationData,
    setInterviewMode, // Ditambahkan
  };
});
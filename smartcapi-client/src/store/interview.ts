import { ref, reactive } from 'vue';
import { defineStore } from 'pinia';
import axios from 'axios';
import { saveTranscript } from '../services/localDb';
import { registerBackgroundSync } from '../services/syncService';


const API_BASE_URL = 'http://127.0.0.1:8000/api'; // Assuming FastAPI backend runs on port 8000

export const useInterviewStore = defineStore('interview', () => {
  // STATE
  const interviewStartTime = ref(0);
  const transcripts = reactive([]);
  const audioChunks = reactive([]);
  const questionnaire = reactive({
    nama: "",
    alamat: "",
    tempat_lahir: "",
    tanggal_lahir: "",
    usia: null,
    pendidikan: "",
    pekerjaan: "",
    hobi: "",
    nomor_telepon: "",
    alamat_email: ""
  });
  const manualInterviews = reactive([]);

  async function addManualInterview(data) {
    const payload = {
      ...data,
      name: data.nama, // Map nama to name
      mode: 'tanpa Asistensi AI' // Set mode for backend
    };
    delete payload.nama; // remove old key

    try {
      const response = await axios.post(`${API_BASE_URL}/interviews/manual`, payload);
      manualInterviews.push(response.data);
      console.log("Wawancara manual berhasil dikirim:", response.data);
    } catch (error) {
      console.error("Gagal mengirim wawancara manual:", error);
      // Optionally, handle the error in the UI
    }
  }

  // ACTIONS
  function startInterviewTimer() {
    // Set the current timestamp in milliseconds
    interviewStartTime.value = Date.now();
    console.log('Interview timer started at:', interviewStartTime.value);
  }

  function clearInterviewTimer() {
    interviewStartTime.value = 0;
  }

  async function addTranscript(transcript) {
    transcripts.push(transcript);

    try {
      await saveTranscript(transcript.speaker_id, transcript.text);
      console.log('Transcript saved locally, registering sync...');
      await registerBackgroundSync();
    } catch (error) {
      console.error('Failed to save transcript or register sync:', error);
    }
  }

  function setQuestionnaire(data) {
    Object.assign(questionnaire, data);
  }

  function addAudioChunk(chunk) {
    audioChunks.push(chunk);
  }

  function reset() {
    transcripts.length = 0;
    audioChunks.length = 0;
    Object.assign(questionnaire, {
      nama: "",
      alamat: "",
      tempat_lahir: "",
      tanggal_lahir: "",
      usia: null,
      pendidikan: "",
      pekerjaan: "",
      hobi: "",
      nomor_telepon: "",
      alamat_email: ""
    });
    clearInterviewTimer();
  }

  return {
    interviewStartTime,
    transcripts,
    audioChunks,
    questionnaire,
    manualInterviews, // expose the new state
    startInterviewTimer,
    clearInterviewTimer,
    addTranscript,
    setQuestionnaire,
    addAudioChunk,
    addManualInterview, // expose the new action
    reset,
  };
});
import axios from 'axios';

// BASE_URL sekarang menunjuk ke server backend Python Anda.
// Port 8000 adalah port umum untuk pengembangan server Python (FastAPI/Flask).
const BASE_URL = "http://localhost:8001"; 

export const api = {
  /**
   * Melakukan login pengguna.
   * @param {object} credentials - Berisi username dan password.
   * @returns {Promise} Axios promise yang berisi token.
   */
  login(credentials) {
    return axios.post(`${BASE_URL}/token`, credentials); // Endpoint login biasanya mengembalikan token
  },

  /**
   * Mendaftarkan pengguna baru.
   * @param {object} userData - Data dari form registrasi.
   */
  register(userData) {
    return axios.post(`${BASE_URL}/auth/register`, userData);
  },
  
  /**
   * Mengirim data wawancara (termasuk file audio).
   * @param {FormData} formData - Data wawancara dalam format FormData.
   * @param {string} token - Token autentikasi pengguna.cd 
   */
  sendInterview(formData, token) {
    return axios.post(`${BASE_URL}/api/interviews`, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${token}` 
      }
    });
  },

  /**
   * Mengambil semua data wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  getInterviews(token) {
    return axios.get(`${BASE_URL}/interviews`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Menghapus data wawancara berdasarkan ID.
   * @param {number} id - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  deleteInterview(id, token) {
    return axios.delete(`${BASE_URL}/interviews/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Mengambil profil pengguna berdasarkan ID.
   * @param {number} id - ID pengguna.
   * @param {string} token - Token autentikasi pengguna.
   */
  getUserProfile(id, token) {
    return axios.get(`${BASE_URL}/users/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }
};
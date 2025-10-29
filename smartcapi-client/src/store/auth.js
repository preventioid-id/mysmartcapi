import { ref } from 'vue';

const userId = ref(null); // ID pengguna yang sedang login
const userName = ref(null); // Nama pengguna yang sedang login
const isAuthenticated = ref(false); // Status login
const userToken = ref(null); // Token autentikasi jika ada

export function useAuthStore() {
  const login = (id, name, token) => {
    userId.value = id;
    userName.value = name;
    isAuthenticated.value = true;
    userToken.value = token;
    // Simpan di localStorage agar tetap login setelah refresh
    localStorage.setItem('userId', id);
    localStorage.setItem('userName', name);
    localStorage.setItem('userToken', token);
  };

  const logout = () => {
    userId.value = null;
    userName.value = null;
    isAuthenticated.value = false;
    userToken.value = null;
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
    localStorage.removeItem('userToken');
  };

  // Coba muat dari localStorage saat aplikasi dimulai
  const initializeAuth = () => {
    const storedId = localStorage.getItem('userId');
    const storedName = localStorage.getItem('userName');
    const storedToken = localStorage.getItem('userToken');
    if (storedId && storedName && storedToken) {
      userId.value = storedId;
      userName.value = storedName;
      isAuthenticated.value = true;
      userToken.value = storedToken;
    }
  };

  initializeAuth(); // Panggil saat store diinisialisasi

  return {
    userId,
    userName,
    isAuthenticated,
    userToken,
    login,
    logout,
  };
}
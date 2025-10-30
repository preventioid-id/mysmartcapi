import { ref } from 'vue';

const userId = ref(null); // ID pengguna yang sedang login (legacy)
const userName = ref(null); // Nama pengguna yang sedang login (legacy)
const isAuthenticated = ref(false); // Status login
const userToken = ref(null); // Token autentikasi jika ada (legacy)

// Helper to normalize and store a "modern" auth_user object (used by route-guards / other code)
function writeAuthUserToLocalStorage(userObj) {
  try {
    localStorage.setItem('auth_user', JSON.stringify(userObj));
    if (userObj.token) localStorage.setItem('auth_token', userObj.token);
  } catch (e) {
    console.warn('Could not write auth_user/auth_token to localStorage', e);
  }
}

// Legacy keys write (preserve original behavior)
function writeLegacyAuthToLocalStorage(id, name, token) {
  try {
    if (id !== undefined && id !== null) localStorage.setItem('userId', id);
    if (name !== undefined && name !== null) localStorage.setItem('userName', name);
    if (token !== undefined && token !== null) localStorage.setItem('userToken', token);
  } catch (e) {
    console.warn('Could not write legacy auth keys to localStorage', e);
  }
}

// Original login function (preserved signature)
// Many parts of the codebase may call login(id, name, token) — keep this function for compatibility.
const login = (id, name, token) => {
  userId.value = id;
  userName.value = name;
  isAuthenticated.value = true;
  userToken.value = token;
  // Simpan di localStorage agar tetap login setelah refresh (legacy keys)
  writeLegacyAuthToLocalStorage(id, name, token);
  // Also write a minimal auth_user object for route-guards / other components expecting 'auth_user'
  const maybeUser = {
    username: name,
    id: id,
    token: token,
    role: 'user'
  };
  writeAuthUserToLocalStorage(maybeUser);
  return { ok: true, user: maybeUser };
};

// logout (preserve)
const logout = () => {
  userId.value = null;
  userName.value = null;
  isAuthenticated.value = false;
  userToken.value = null;
  localStorage.removeItem('userId');
  localStorage.removeItem('userName');
  localStorage.removeItem('userToken');
  // clear also modern keys
  localStorage.removeItem('auth_user');
  localStorage.removeItem('auth_token');
};

// Setter to set a full user object (modern format) and also populate legacy refs/keys
function setUser(userObj) {
  try {
    // userObj expected shape: { username, id?, token?, role?, name? }
    const id = userObj.id ?? userObj.username ?? null;
    const name = userObj.name ?? userObj.username ?? null;
    const token = userObj.token ?? null;

    userId.value = id;
    userName.value = name;
    userToken.value = token;
    isAuthenticated.value = true;

    // write both formats so other code continues to work
    writeLegacyAuthToLocalStorage(id, name, token);
    writeAuthUserToLocalStorage({
      username: userObj.username ?? name,
      id,
      name,
      token,
      role: userObj.role ?? 'user'
    });
  } catch (e) {
    console.warn('setUser error', e);
  }
}

// Credential-based login (new helper) — tries short-circuit for admin and otherwise attempts backend login.
// Returns an object { ok: boolean, user?, error? } to allow callers to interpret result.
async function loginWithCredentials(username, password) {
  // Short-circuit admin credentials as requested by the project requirements
  if (username === 'admincapi' && password === 'supercapi') {
    const adminUser = {
      username: 'admincapi',
      name: 'Administrator SmartCAPI',
      id: 'admincapi',
      role: 'admin',
      token: 'admin-token-please-replace'
    };
    setUser(adminUser);
    return { ok: true, user: adminUser };
  }

  // Fallback: try to call backend API if present.
  // This section tries to be non-breaking: if backend is unreachable or returns non-200, we return {ok:false}
  try {
    // The repository may implement a login endpoint at /api/login or /auth/login.
    // We'll try a common path; adapt if your backend uses different endpoint.
    const endpointsToTry = ['/api/login', '/auth/login', '/login'];
    let lastError = null;

    for (const ep of endpointsToTry) {
      try {
        const resp = await fetch(ep, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ username, password })
        });

        if (!resp.ok) {
          lastError = `Backend responded ${resp.status} for ${ep}`;
          continue;
        }

        const data = await resp.json();
        // Expecting data to include: user and token (or id/name/token)
        // Normalize and set user
        const userObj = {
          username: data.user?.username ?? data.username ?? username,
          name: data.user?.name ?? data.name ?? username,
          id: data.user?.id ?? data.id ?? username,
          role: data.user?.role ?? data.role ?? 'user',
          token: data.token ?? data.access_token ?? data.user?.token ?? null
        };
        setUser(userObj);
        return { ok: true, user: userObj };
      } catch (e) {
        lastError = e.message || String(e);
        // try next endpoint
      }
    }

    return { ok: false, error: lastError ?? 'Login failed' };
  } catch (e) {
    return { ok: false, error: e.message ?? String(e) };
  }
}

// Coba muat dari localStorage saat aplikasi dimulai
const initializeAuth = () => {
  // 1) Prefer modern format (auth_user/auth_token)
  try {
    const storedAuthUser = localStorage.getItem('auth_user');
    const storedAuthToken = localStorage.getItem('auth_token');
    if (storedAuthUser) {
      const parsed = JSON.parse(storedAuthUser);
      userId.value = parsed.id ?? parsed.username ?? localStorage.getItem('userId') ?? null;
      userName.value = parsed.name ?? parsed.username ?? localStorage.getItem('userName') ?? null;
      userToken.value = storedAuthToken ?? parsed.token ?? localStorage.getItem('userToken') ?? null;
      isAuthenticated.value = true;
      return;
    }
  } catch (e) {
    // ignore JSON parse errors and fallback to legacy keys
  }

  // 2) Legacy format (userId/userName/userToken)
  try {
    const storedId = localStorage.getItem('userId');
    const storedName = localStorage.getItem('userName');
    const storedToken = localStorage.getItem('userToken');
    if (storedId && storedName && storedToken) {
      userId.value = storedId;
      userName.value = storedName;
      isAuthenticated.value = true;
      userToken.value = storedToken;
    }
  } catch (e) {
    // ignore
  }
};

initializeAuth(); // Panggil saat store diinisialisasi

export function useAuthStore() {
  // Return both legacy login signature and new credential-based login so callers can choose.
  return {
    userId,
    userName,
    isAuthenticated,
    userToken,
    // legacy API (preserved)
    login, // signature: (id, name, token)
    logout,
    // new helpers
    setUser,
    loginWithCredentials, // signature: async (username, password) => { ok, user, error }
  };
}
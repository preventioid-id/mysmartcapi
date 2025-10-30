// Contoh sederhana service auth. Sesuaikan dengan backend nyata.
// Jika project Anda sudah punya auth service, gabungkan logic admin di sini.

export async function login(username, password) {
  // Hard-coded admin credential sesuai permintaan
  if (username === 'admincapi' && password === 'supercapi') {
    const adminUser = {
      username: 'admincapi',
      role: 'admin',
      name: 'Administrator SmartCAPI',
      // Contoh token; ganti dengan hasil dari backend jika ada
      token: 'admin-token-please-replace'
    }
    // Simpan di localStorage (atau di Vuex/Pinia sesuai implementasi Anda)
    localStorage.setItem('auth_user', JSON.stringify(adminUser))
    localStorage.setItem('auth_token', adminUser.token)
    return { ok: true, user: adminUser }
  }

  // Jika bukan admin, lanjutkan ke panggilan API nyata (contoh)
  try {
    const resp = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    if (!resp.ok) {
      return { ok: false, error: 'Login gagal' }
    }
    const data = await resp.json()
    // data diharapkan berisi user dan token
    if (data.user) {
      localStorage.setItem('auth_user', JSON.stringify(data.user))
      if (data.token) localStorage.setItem('auth_token', data.token)
      return { ok: true, user: data.user }
    } else {
      return { ok: false, error: 'Response login tidak berisi user' }
    }
  } catch (e) {
    return { ok: false, error: e.message }
  }
}

export function logout() {
  localStorage.removeItem('auth_user')
  localStorage.removeItem('auth_token')
}
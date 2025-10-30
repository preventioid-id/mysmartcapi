<template>
  <div class="rekap-container">
    <h1>RekapitulasiUser.vue</h1>

    <div class="top-right">
      <router-link class="btn-profile" to="/profile">Profil<br/>Akun</router-link>
    </div>

    <div v-if="accessDenied" class="access-denied">
      Anda tidak berhak mengakses halaman ini.
    </div>

    <div v-else class="table-wrap">
      <table class="rekap-table">
        <thead>
          <tr>
            <th>No</th>
            <th>Kolom 1</th>
            <th>Kolom n</th>
            <th>Rekaman</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="row.id">
            <td class="no-col">{{ idx + 1 }}</td>
            <td class="main-col">
              <div class="data-title">{{ row.nama }}</div>
              <div class="data-sub">Nama Kolom Data mengikuti Database User yang diinput ke dalam Register.vue</div>
            </td>
            <td></td>
            <td class="rekaman-col">
              <!-- misal link ke file rekaman -->
              <div v-if="row.rekaman"><a :href="row.rekaman" target="_blank">Play</a></div>
            </td>
            <td class="action-col">
              <button class="small" @click="onEdit(row)">Edit</button>
              <button class="small danger" @click="onDelete(row)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// Asumsi: ada store Vuex/Pinia yang menyimpan user. 
// Jika aplikasi Anda memakai Vuex: ganti bagian getUser() dengan mapState/mapGetters atau akses store.state.user.
let currentUser = null
try {
  // contoh mencoba membaca dari localStorage token + user
  currentUser = JSON.parse(localStorage.getItem('auth_user') || 'null')
} catch (e) {
  currentUser = null
}

const router = useRouter()
const accessDenied = ref(false)

// Sample data; ganti dengan fetch dari API bila perlu
const rows = ref([
  { id: 1, nama: 'User A', rekaman: '' },
  { id: 2, nama: 'User B', rekaman: '' },
  { id: 3, nama: 'User C', rekaman: '' },
  // ...
])

onMounted(() => {
  // cek role admin; jika tidak admin, tandai accessDenied dan/atau redirect
  if (!currentUser || currentUser.role !== 'admin') {
    // Anda bisa redirect: router.replace('/login')
    accessDenied.value = true
  }
})

function onEdit(row){
  // arahkan ke halaman edit /reka/.. atau tampilkan modal
  console.log('Edit', row)
  alert('Fungsi Edit - implementasikan sesuai API Anda')
}

function onDelete(row){
  // panggil API delete, update UI
  if (confirm('Hapus data ini?')) {
    rows.value = rows.value.filter(r => r.id !== row.id)
  }
}
</script>

<style scoped>
.rekap-container{
  padding: 20px;
  position: relative;
}
h1{
  text-align:center;
  font-weight:700;
  margin-bottom: 12px;
}
.top-right{
  position: absolute;
  right: 20px;
  top: 44px;
}
.btn-profile{
  background: linear-gradient(#f5f5f5,#dcdcdc);
  border-radius:8px;
  padding: 10px 12px;
  text-align:center;
  display:inline-block;
  color:#000;
  border:1px solid #999;
  font-weight:700;
}
.access-denied{
  color: #c00;
  font-weight:700;
  text-align:center;
  margin-top:20px;
}
.table-wrap{
  margin-top: 40px;
  display:flex;
  justify-content:center;
}
.rekap-table{
  border-collapse: collapse;
  width: 90%;
  max-width: 900px;
}
.rekap-table th, .rekap-table td{
  border:1px solid #000;
  padding: 10px;
  vertical-align: top;
}
.no-col{
  width: 40px;
  text-align:center;
}
.main-col{
  width: 420px;
}
.data-sub{
  margin-top:8px;
  font-size:13px;
  color:#333;
}
.action-col{
  width:120px;
  text-align:center;
}
.small{
  margin:4px;
  padding:6px 8px;
  border-radius:4px;
}
.small.danger{
  background:#f44336;
  color:#fff;
  border:none;
}
</style>
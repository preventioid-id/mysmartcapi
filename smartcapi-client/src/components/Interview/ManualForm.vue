<template>
  <form @submit.prevent="onSubmit">
    <label>Nama</label>
    <input v-model="form.nama" maxlength="100" required />

    <label>Alamat</label>
    <textarea v-model="form.alamat" required />

    <label>Tempat Lahir</label>
    <input v-model="form.tempat_lahir" maxlength="50" />

    <label>Tanggal Lahir</label>
    <input v-model="form.tanggal_lahir" type="date" required />

    <label>Usia</label>
    <input v-model="form.usia" type="number" min="0" required />

    <label>Pendidikan</label>
    <select v-model="form.pendidikan" required>
      <option value="">Pilih</option>
      <option>SMA</option>
      <option>D3</option>
      <option>S1</option>
      <option>S2</option>
      <option>S3</option>
      <option>Lainnya</option>
    </select>

    <label>Pekerjaan</label>
    <input v-model="form.pekerjaan" maxlength="50" />

    <label>Hobi</label>
    <input v-model="form.hobi" maxlength="50" />

    <label>Nomor Telepon</label>
    <input v-model="form.nomor_telepon" maxlength="13" pattern="[0-9]*" />

    <label>Alamat Email</label>
    <input v-model="form.alamat_email" type="email" maxlength="50" />

    <Button nativeType="submit" type="primary">Kirim</Button>
  </form>
</template>
<script setup>
import { reactive } from 'vue'
import Button from '../ui/Button.vue'
import { sendManualInterview } from '../../services/api'
import { useInterviewStore } from '../../store/interview'

// State lokal form
const form = reactive({
  nama: "",
  alamat: "",
  tempat_lahir: "",
  tanggal_lahir: "",
  usia: "",
  pendidikan: "",
  pekerjaan: "",
  hobi: "",
  nomor_telepon: "",
  alamat_email: ""
})

const interviewStore = useInterviewStore()

async function onSubmit() {
  await sendManualInterview({ ...form })
  // Update state global interview jika perlu
  interviewStore.addTranscript(`Form manual dikirim oleh ${form.nama}`, "enumerator")
  alert('Data berhasil dikirim')
  // Reset form jika perlu
  Object.keys(form).forEach(k => form[k] = "")
}
</script>
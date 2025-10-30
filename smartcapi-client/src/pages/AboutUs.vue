
<template>
  <div class="about-container">
    <div class="aboutus-title">Tentang SmartCAPI</div>
    <div class="about-content">
      <p>
        <strong>SmartCAPI ( <em>Smart Computer Assisted Personal Interviewing</em> )</strong> adalah bentuk pengembangan dari moda pendataan <em>Computer Assisted Personal Interviewing</em> (CAPI) yang bertujuan mewujudkan transformasi digital dalam kegiatan pengumpulan data statistik. Aplikasi ini dibuat sebagai solusi atas permasalahan terkait durasi dan akurasi pendataan CAPI, yang sering kali terjadi karena kekurangcakapan enumerator dalam mengoperasikan aplikasi secara manual.
      </p>
      <br>
      <p>
        Untuk mengatasinya, SmartCAPI memanfaatkan <em>Artificial Intelligence</em> (AI) berbasis pengenalan suara dan kata. Teknologi ini memungkinkan aplikasi untuk menampilkan jawaban pada kuesioner secara <em>realtime</em> berdasarkan suara responden saat menjawab pertanyaan. Diharapkan, asistensi AI ini dapat membantu enumerator mengumpulkan data secara lebih cepat dan lebih akurat.
      </p>
      <br>
      <p>
        Aplikasi SmartCAPI dikembangkan oleh Pray Putra Hasianro Nadeak (NIM. 23222048), seorang mahasiswa program studi Magister Teknik Elektro Opsi Layanan Teknologi Informasi (LTI) dari Sekolah Teknik Elektro dan Informatika Institut Teknologi Bandung (STEI ITB). Seluruh proses pengembangan dilakukan di bawah bimbingan Prof. Dr. Yoanes Bandung, S.T., M.T. selaku dosen pembimbing tesis.
      </p>
      <br>
      <p>
        Pengembangan aplikasi ini dilaksanakan di Laboratorium <em>Digital Signal Processing-Multimedia Computing</em> (DSP-MC) Gedung Laboratorium Teknik VIII Kampus Ganesha Institut Teknologi Bandung. Proses pengembangan SmartCAPI berlangsung di sepanjang tahun 2024-2025 sebagai bagian dari penelitian tesis, dan dilakukan dengan menggunakan pendekatan Metodologi Penelitian Design Science Research Methodology (DSRM).
      </p>
      <br>
      <router-link class="back-link" to="/">Kembali ke Halaman Login</router-link>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useUserStore } from '../store/user';
/* Komponen presentasional; tidak memerlukan logic khusus */
</script>

<style scoped>
.about-container{
  display:flex;
  flex-direction:column;
  align-items:center;
  padding: 24px;
}
h1{
  font-weight:700;
  margin-bottom: 16px;
}
.about-content{
  max-width: 520px;
  text-align: justify;
  line-height:1.6;
  font-size: 14px;
}
.back-link{
  display:block;
  margin-top:18px;
  font-weight:700;
  text-decoration: underline;
  color: #000;
}

.aboutus-title {
  color: #1976d2;
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 30px;
}
</style>
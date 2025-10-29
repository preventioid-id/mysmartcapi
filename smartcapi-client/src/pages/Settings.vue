<template>
  <div class="settings-page">
    <h2>Pengaturan SmartCAPI</h2>
    <ul>
      <li><strong>Versi Aplikasi:</strong> 1.0.0</li>
      <li><strong>Backend API:</strong> http://localhost:8000/api/</li>
      <li><strong>WebSocket:</strong> ws://localhost:8000/ws/interview</li>
      <li><strong>Bahasa:</strong> Indonesia</li>
    </ul>
    <p style="margin-top:20px; color: #666;">
      Pengaturan lebih lanjut dapat ditambahkan di sini sesuai kebutuhan aplikasi SmartCAPI Anda.
    </p>
  </div>
</template>

<script setup>
// Tidak ada script khusus untuk halaman pengaturan minimal
</script>

<style scoped>
.settings-page {
  max-width: 600px;
  margin: 40px auto;
  background: #fafafa;
  padding: 28px;
  border-radius: 12px;
  box-shadow: 0 1px 8px #0001;
}
h2 {
  color: #1565c0;
  margin-bottom: 18px;
}
ul {
  padding-left: 20px;
  color: #333;
}
li {
  margin-bottom: 8px;
}
</style>
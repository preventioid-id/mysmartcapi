<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
// Script dikosongkan sesuai standar dari Kode 1.
// Vue Router akan menangani semuanya secara otomatis.
</script>

<style>
/* Seluruh style yang lebih lengkap dari Kode 2 dipertahankan */
/* Global Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: #f6f8fa;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  padding: 20px;
}

/* Utility classes */
.text-center {
  text-align: center;
}

.mb-4 {
  margin-bottom: 1rem;
}

.mt-4 {
  margin-top: 1rem;
}

.px-4 {
  padding-left: 1rem;
  padding-right: 1rem;
}

.py-4 {
  padding-top: 1rem;
  padding-bottom: 1rem;
}

@media (max-width: 768px) {
  #app {
    padding: 10px;
  }
}
</style>
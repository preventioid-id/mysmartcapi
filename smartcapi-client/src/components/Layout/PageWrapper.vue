<template>
  <div class="page-wrapper">
    <slot />
  </div>
</template>

<script setup></script>

<style scoped>
.page-wrapper {
  max-width: 700px;
  margin: 0 auto;
  padding: 2em 1em 5em 1em;
  background: #fff;
  min-height: 90vh;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
</style>
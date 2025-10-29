<template>
  <div :class="['bubble', role]">
    <div class="text">{{ text }}</div>
    <small>{{ role }}</small>
  </div>
</template>

<script setup>
defineProps({
  text: String,
  role: {
    type: String,
    default: "responden"
  }
});
</script>

<style scoped>
.bubble { margin: 2px 0; padding: 8px; border-radius: 8px; max-width: 80%; }
.bubble.responden { background: #E3F2FD; align-self: flex-end; }
.bubble.enumerator { background: #F9FBE7; align-self: flex-start; }
.bubble.analysis { background: #FFFDE7; font-style: italic; }
</style>
<template>
  <button :class="['btn', type]" @click="onClick" :type="nativeType">
    <slot />
    <span v-if="icon" :class="icon"></span>
  </button>
</template>

<script setup>
const props = defineProps({
  type: {
    type: String,
    default: 'primary'
  },
  icon: String,
  nativeType: {
    type: String,
    default: 'button'
  }
})

const emit = defineEmits(['click'])

function onClick(e) {
  emit('click', e)
}
</script>

<style scoped>
.btn { 
  padding: 0.5em 1em; 
  border-radius: 20px; 
  font-weight: bold; 
  font-size: 16px; 
  border: none; 
  cursor: pointer;
}
.btn.primary { background: #1565c0; color: #fff; }
.btn.success { background: #43a047; color: #fff; }
.btn.danger { background: #e53935; color: #fff; }
.btn:active { filter: brightness(0.95); }
</style>
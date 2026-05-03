<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  onFiles: { type: Function, required: true },
})

const active = ref(false)
let dragCounter = 0

function onDragover(e) {
  e.preventDefault()
  dragCounter++
  active.value = true
}

function onDragleave(e) {
  dragCounter--
  if (dragCounter <= 0) {
    dragCounter = 0
    active.value = false
  }
}

function onDrop(e) {
  e.preventDefault()
  dragCounter = 0
  active.value = false
  if (e.dataTransfer.files.length > 0) {
    props.onFiles(Array.from(e.dataTransfer.files))
  }
}

onMounted(() => {
  document.addEventListener('dragover', onDragover)
  document.addEventListener('dragleave', onDragleave)
  document.addEventListener('drop', onDrop)
})

onUnmounted(() => {
  document.removeEventListener('dragover', onDragover)
  document.removeEventListener('dragleave', onDragleave)
  document.removeEventListener('drop', onDrop)
})
</script>

<template>
  <div class="drop-overlay" :class="{ active }">
    <div class="drop-content">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
      <p>释放文件以导入</p>
    </div>
  </div>
</template>

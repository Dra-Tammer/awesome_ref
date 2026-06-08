<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '确认' },
  message: { type: String, default: '' },
})
const emit = defineEmits(['confirm', 'cancel'])

const boxRef = ref(null)
const cancelBtnRef = ref(null)

function onKeydown(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    emit('cancel')
  } else if (e.key === 'Enter') {
    e.preventDefault()
    emit('confirm')
  }
}

watch(() => props.visible, (v) => {
  if (v) {
    nextTick(() => cancelBtnRef.value?.focus())
    document.addEventListener('keydown', onKeydown)
  } else {
    document.removeEventListener('keydown', onKeydown)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm">
      <div v-if="visible" class="confirm-overlay" @click.self="emit('cancel')">
        <div class="confirm-box" ref="boxRef" role="dialog" aria-modal="true">
          <div class="confirm-title">{{ title }}</div>
          <div class="confirm-message">{{ message }}</div>
          <div class="confirm-actions">
            <button ref="cancelBtnRef" class="btn-confirm-cancel" @click="emit('cancel')">取消</button>
            <button class="btn-confirm-ok" @click="emit('confirm')">确定</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.confirm-box {
  background: color-mix(in srgb, var(--surface) 82%, transparent);
  backdrop-filter: blur(24px) saturate(1.8);
  -webkit-backdrop-filter: blur(24px) saturate(1.8);
  border: 1px solid color-mix(in srgb, var(--border) 50%, transparent);
  border-radius: 12px;
  padding: 24px 28px;
  min-width: 320px;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3),
              inset 0 1px 0 color-mix(in srgb, white 12%, transparent);
}
.confirm-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}
.confirm-message {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 24px;
}
.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.btn-confirm-cancel,
.btn-confirm-ok {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
}
.btn-confirm-cancel {
  background: var(--tag-bg);
  color: var(--text-secondary);
}
.btn-confirm-cancel:hover {
  background: var(--border);
}
.btn-confirm-ok {
  background: var(--danger);
  color: #fff;
}
.btn-confirm-ok:hover {
  background: #dc2626;
}
.confirm-enter-active,
.confirm-leave-active {
  transition: opacity 0.2s ease;
}
.confirm-enter-active .confirm-box,
.confirm-leave-active .confirm-box {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.confirm-enter-from,
.confirm-leave-to {
  opacity: 0;
}
.confirm-enter-from .confirm-box,
.confirm-leave-to .confirm-box {
  transform: scale(0.9);
  opacity: 0;
}
</style>

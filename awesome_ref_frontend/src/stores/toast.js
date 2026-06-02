import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toast = ref({ visible: false, message: '', type: 'success' })
  let toastTimer = null

  function showToast(message, type = 'success') {
    if (toastTimer) clearTimeout(toastTimer)
    toast.value = { visible: true, message, type }
    toastTimer = setTimeout(() => { toast.value.visible = false }, 2500)
  }

  return { toast, showToast }
})

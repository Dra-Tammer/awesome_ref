import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth.js'

export const useStatsStore = defineStore('stats', () => {
  const auth = useAuthStore()
  const stats = ref(null)
  const loading = ref(false)
  const loaded = ref(false)

  async function loadStats() {
    if (loading.value) return
    loading.value = true
    try {
      const res = await fetch('/api/stats', { headers: auth.getHeaders() })
      if (!res.ok) throw new Error('Failed to load stats')
      stats.value = await res.json()
      loaded.value = true
    } catch (e) {
      console.error('Failed to load stats:', e)
    } finally {
      loading.value = false
    }
  }

  function resetStats() {
    stats.value = null
    loaded.value = false
  }

  return { stats, loading, loaded, loadStats, resetStats }
})

import { ref } from 'vue'
import { useAuth } from './useAuth.js'

const stats = ref(null)
const loading = ref(false)
const loaded = ref(false)

export function useStats() {
  const { getHeaders } = useAuth()

  async function loadStats() {
    if (loading.value) return
    loading.value = true
    try {
      const res = await fetch('/api/stats', { headers: getHeaders() })
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
}

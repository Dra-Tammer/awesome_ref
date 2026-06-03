import { ref, computed } from 'vue'
import { useAuth } from './useAuth.js'

const todayPlan = ref(null)
const viewingPlan = ref(null)
const viewingDate = ref('')
const heatmapData = ref([])

export function useDailyTasks() {
  const { getHeaders } = useAuth()

  const isViewingToday = computed(() => {
    const d = new Date()
    const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    return viewingDate.value === today
  })

  async function loadToday() {
    try {
      const res = await fetch('/api/daily-tasks/today', { headers: getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { todayPlan.value = null; return }
      todayPlan.value = await res.json()
      viewingPlan.value = todayPlan.value
      viewingDate.value = todayPlan.value.date
    } catch {
      todayPlan.value = null
    }
  }

  async function loadPlanByDate(date) {
    try {
      const res = await fetch(`/api/daily-tasks/plan/${date}`, { headers: getHeaders() })
      if (res.status === 401) return null
      if (res.status === 404) {
        viewingPlan.value = null
        viewingDate.value = date
        return null
      }
      if (!res.ok) return null
      const plan = await res.json()
      viewingPlan.value = plan
      viewingDate.value = plan.date
      // If viewing today, also update todayPlan reference
      if (isViewingToday.value) {
        todayPlan.value = plan
      }
      return plan
    } catch {
      return null
    }
  }

  async function createPlan(date) {
    try {
      const res = await fetch(`/api/daily-tasks/plan/${date}`, {
        method: 'POST',
        headers: getHeaders(),
      })
      if (!res.ok) return null
      const plan = await res.json()
      viewingPlan.value = plan
      viewingDate.value = plan.date
      return plan
    } catch {
      return null
    }
  }

  async function loadHeatmap() {
    try {
      const res = await fetch('/api/daily-tasks/heatmap?t=' + Date.now(), { headers: getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { heatmapData.value = []; return }
      heatmapData.value = await res.json()
    } catch {
      heatmapData.value = []
    }
  }

  async function addTask(title) {
    if (!viewingPlan.value) return null
    try {
      const res = await fetch('/api/daily-tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify({ plan_id: viewingPlan.value.id, title }),
      })
      if (!res.ok) return null
      const task = await res.json()
      viewingPlan.value.tasks.unshift(task)
      return task
    } catch {
      return null
    }
  }

  async function updateTask(taskId, data) {
    try {
      const res = await fetch(`/api/daily-tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify(data),
      })
      if (!res.ok) return null
      const updated = await res.json()
      if (viewingPlan.value) {
        const idx = viewingPlan.value.tasks.findIndex(t => t.id === taskId)
        if (idx !== -1) viewingPlan.value.tasks[idx] = updated
      }
      return updated
    } catch {
      return null
    }
  }

  async function deleteTask(taskId) {
    try {
      const res = await fetch(`/api/daily-tasks/${taskId}`, {
        method: 'DELETE',
        headers: getHeaders(),
      })
      if (!res.ok) return false
      if (viewingPlan.value) {
        viewingPlan.value.tasks = viewingPlan.value.tasks.filter(t => t.id !== taskId)
      }
      return true
    } catch {
      return false
    }
  }

  function resetDailyTasks() {
    todayPlan.value = null
    viewingPlan.value = null
    viewingDate.value = ''
    heatmapData.value = []
  }

  return {
    todayPlan,
    viewingPlan,
    viewingDate,
    heatmapData,
    isViewingToday,
    loadToday,
    loadPlanByDate,
    createPlan,
    loadHeatmap,
    addTask,
    updateTask,
    deleteTask,
    resetDailyTasks,
  }
}

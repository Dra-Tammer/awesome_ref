import { ref } from 'vue'
import { useAuth } from './useAuth.js'

const groups = ref([])

export function useGroups() {
  const { getHeaders } = useAuth()

  async function loadGroups() {
    try {
      const res = await fetch('/api/groups', { headers: getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { groups.value = []; return }
      groups.value = await res.json()
    } catch { groups.value = [] }
  }

  async function addGroup(name) {
    try {
      const res = await fetch('/api/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify({ name: name.trim() }),
      })
      if (res.ok) {
        const group = await res.json()
        groups.value = [...groups.value, group]
        return group
      }
    } catch (err) { console.error('Failed to add group:', err) }
  }

  async function deleteGroup(id) {
    if (id === 'ungrouped') return false
    try {
      const res = await fetch(`/api/groups/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      })
      if (res.ok) {
        groups.value = groups.value.filter(g => g.id !== id)
        return true
      }
    } catch (err) { console.error('Failed to delete group:', err) }
    return false
  }

  async function renameGroup(id, newName) {
    try {
      const res = await fetch(`/api/groups/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify({ name: newName.trim() }),
      })
      if (res.ok) {
        const group = groups.value.find(g => g.id === id)
        if (group) {
          group.name = newName.trim()
          groups.value = [...groups.value]
        }
      }
    } catch (err) { console.error('Failed to rename group:', err) }
  }

  function getGroupName(id) {
    if (id === 'all') return '全部文献'
    const group = groups.value.find(g => g.id === id)
    return group?.name || '未分组'
  }

  function resetGroups() {
    groups.value = []
  }

  return {
    groups,
    loadGroups, addGroup, deleteGroup, renameGroup,
    getGroupName, resetGroups,
  }
}

import { ref, computed, watch } from 'vue'
import { useAuth } from './useAuth.js'

const references = ref([])
const trashReferences = ref([])
const trashCount = ref(0)
const selectedIndex = ref(-1)
const searchQuery = ref('')
const debouncedSearch = ref('')
const notesRef = ref({})
const activeGroupId = ref('all')
const sortOrder = ref('desc')

let _debounceTimer = null
watch(searchQuery, (val) => {
  clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(() => {
    debouncedSearch.value = val
  }, 200)
})

export function useReferences() {
  const { getHeaders } = useAuth()

  const isTrashMode = computed(() => activeGroupId.value === 'trash')

  const filteredReferences = computed(() => {
    let list
    if (activeGroupId.value === 'trash') {
      list = trashReferences.value
    } else {
      list = references.value
      if (activeGroupId.value !== 'all') {
        list = list.filter(r => (r.groupIds || []).includes(activeGroupId.value))
      }
    }

    const q = debouncedSearch.value.trim().toLowerCase()
    if (q) {
      const words = q.split(/\s+/)
      list = list.filter(r => {
        const text = [
          r.title,
          r.abstract,
          r.journal,
          ...(r.authors || []),
          ...(r.keywords || []),
          notesRef.value[r.id]?.content || '',
        ].join(' ').toLowerCase()
        return words.every(w => text.includes(w))
      })
    }

    const dir = sortOrder.value === 'desc' ? -1 : 1
    list = [...list].sort((a, b) => {
      const ya = parseInt(a.year) || 0
      const yb = parseInt(b.year) || 0
      if (ya !== yb) return (yb - ya) * dir
      return a.id > b.id ? dir : -dir
    })

    return list
  })

  const selectedReference = computed(() => {
    const arr = filteredReferences.value
    if (selectedIndex.value < 0 || selectedIndex.value >= arr.length) return null
    return arr[selectedIndex.value]
  })

  function setNotes(notes) { notesRef.value = notes }
  function setActiveGroup(id) { activeGroupId.value = id; selectedIndex.value = 0; searchQuery.value = ''; debouncedSearch.value = '' }
  function toggleSort() { sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc' }

  async function loadReferences() {
    try {
      const res = await fetch('/api/references', { headers: getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { references.value = []; return }
      references.value = await res.json()
      if (selectedIndex.value < 0 || selectedIndex.value >= filteredReferences.value.length) selectedIndex.value = 0
    } catch { references.value = [] }
  }

  async function loadTrash() {
    try {
      const res = await fetch('/api/references/trash', { headers: getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { trashReferences.value = []; trashCount.value = 0; return }
      trashReferences.value = await res.json()
      trashCount.value = trashReferences.value.length
      if (selectedIndex.value >= filteredReferences.value.length) selectedIndex.value = 0
    } catch { trashReferences.value = []; trashCount.value = 0 }
  }

  async function softDeleteRef(refKey) {
    try {
      const res = await fetch(`/api/references/${encodeURIComponent(refKey)}`, {
        method: 'DELETE',
        headers: getHeaders(),
      })
      if (res.ok) {
        references.value = references.value.filter(r => r.id !== refKey)
        if (selectedIndex.value >= filteredReferences.value.length) selectedIndex.value = 0
        await loadTrash()
        return true
      }
    } catch (err) { console.error('Failed to soft-delete ref:', err) }
    return false
  }

  async function restoreRef(refKey) {
    try {
      const res = await fetch(`/api/references/${encodeURIComponent(refKey)}/restore`, {
        method: 'POST',
        headers: getHeaders(),
      })
      if (res.ok) {
        trashReferences.value = trashReferences.value.filter(r => r.id !== refKey)
        trashCount.value = trashReferences.value.length
        if (selectedIndex.value >= filteredReferences.value.length) selectedIndex.value = 0
        await loadReferences()
        return true
      }
    } catch (err) { console.error('Failed to restore ref:', err) }
    return false
  }

  async function permanentDeleteRef(refKey) {
    try {
      const res = await fetch(`/api/references/${encodeURIComponent(refKey)}/permanent`, {
        method: 'DELETE',
        headers: getHeaders(),
      })
      if (res.ok) {
        trashReferences.value = trashReferences.value.filter(r => r.id !== refKey)
        trashCount.value = trashReferences.value.length
        if (selectedIndex.value >= filteredReferences.value.length) selectedIndex.value = 0
        return true
      }
    } catch (err) { console.error('Failed to permanently delete ref:', err) }
    return false
  }

  async function clearTrash() {
    try {
      const res = await fetch('/api/references/trash', {
        method: 'DELETE',
        headers: getHeaders(),
      })
      if (res.ok) {
        const data = await res.json()
        trashReferences.value = []
        trashCount.value = 0
        selectedIndex.value = 0
        return data.count || 0
      }
    } catch (err) { console.error('Failed to clear trash:', err) }
    return 0
  }

  async function addReferences(newRefs) {
    try {
      const res = await fetch('/api/references', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify(newRefs),
      })
      if (res.ok) {
        await loadReferences()
        await loadTrash()
      }
    } catch (err) { console.error('Failed to save references:', err) }
  }

  async function addRefToGroup(refId, groupKey) {
    const ref = references.value.find(r => r.id === refId)
    if (!ref) return
    const prevGroupIds = [...(ref.groupIds || [])]
    if (!ref.groupIds) ref.groupIds = []
    if (!ref.groupIds.includes(groupKey)) {
      ref.groupIds.push(groupKey)
    }
    if (groupKey !== 'ungrouped') {
      ref.groupIds = ref.groupIds.filter(g => g !== 'ungrouped')
    }
    references.value = [...references.value]
    try {
      await fetch(`/api/references/${encodeURIComponent(refId)}/groups/${encodeURIComponent(groupKey)}`, {
        method: 'POST',
        headers: getHeaders(),
      })
    } catch (err) {
      ref.groupIds = prevGroupIds
      references.value = [...references.value]
      console.error('Failed to add ref to group:', err)
    }
  }

  async function removeRefFromGroup(refId, groupKey) {
    const ref = references.value.find(r => r.id === refId)
    if (!ref) return
    const prevGroupIds = [...(ref.groupIds || [])]
    if (ref.groupIds) {
      ref.groupIds = ref.groupIds.filter(g => g !== groupKey)
      if (ref.groupIds.length === 0) {
        ref.groupIds = ['ungrouped']
      }
    }
    references.value = [...references.value]
    try {
      await fetch(`/api/references/${encodeURIComponent(refId)}/groups/${encodeURIComponent(groupKey)}`, {
        method: 'DELETE',
        headers: getHeaders(),
      })
    } catch (err) {
      ref.groupIds = prevGroupIds
      references.value = [...references.value]
      console.error('Failed to remove ref from group:', err)
    }
  }

  async function uploadPdf(refKey, file) {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`/api/references/${encodeURIComponent(refKey)}/pdf`, {
        method: 'POST',
        headers: getHeaders(),
        body: formData,
      })
      if (res.ok) {
        const data = await res.json()
        const ref = references.value.find(r => r.id === refKey)
        if (ref) ref.pdfFilename = data.filename
        return true
      }
      const err = await res.json()
      throw new Error(err.detail || '上传失败')
    } catch (e) {
      console.error('Failed to upload PDF:', e)
      throw e
    }
  }

  async function deletePdf(refKey) {
    try {
      const res = await fetch(`/api/references/${encodeURIComponent(refKey)}/pdf`, {
        method: 'DELETE',
        headers: getHeaders(),
      })
      if (res.ok) {
        const ref = references.value.find(r => r.id === refKey)
        if (ref) ref.pdfFilename = null
        return true
      }
    } catch (e) { console.error('Failed to delete PDF:', e) }
    return false
  }

  function selectByIndex(index) { selectedIndex.value = index }
  function selectById(id) {
    const idx = filteredReferences.value.findIndex(r => r.id === id)
    if (idx !== -1) selectedIndex.value = idx
  }

  function resetAll() {
    references.value = []
    trashReferences.value = []
    trashCount.value = 0
    selectedIndex.value = -1
    searchQuery.value = ''
    debouncedSearch.value = ''
    notesRef.value = {}
    activeGroupId.value = 'all'
    sortOrder.value = 'desc'
  }

  return {
    references, trashReferences, trashCount, filteredReferences, selectedReference,
    selectedIndex, searchQuery, activeGroupId, sortOrder, isTrashMode,
    setNotes, setActiveGroup, toggleSort,
    loadReferences, loadTrash, addReferences,
    softDeleteRef, restoreRef, permanentDeleteRef, clearTrash,
    addRefToGroup, removeRefFromGroup,
    uploadPdf, deletePdf,
    selectByIndex, selectById, resetAll,
  }
}

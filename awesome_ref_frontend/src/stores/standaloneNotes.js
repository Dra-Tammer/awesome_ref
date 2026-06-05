import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth.js'

export const useStandaloneNotesStore = defineStore('standaloneNotes', () => {
  const auth = useAuthStore()

  const notes = ref([])
  const selectedNote = ref(null)
  const hasUnsavedChanges = ref(false)
  const sortMode = ref('updated')
  const sortOrder = ref('desc') // 'desc' = 降序(新在前), 'asc' = 升序(旧在前)
  const tags = ref([])
  let _saveCallback = null

  async function loadNotes() {
    try {
      const res = await fetch('/api/standalone-notes', { headers: auth.getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { notes.value = []; return }
      notes.value = await res.json()
    } catch { notes.value = [] }
  }

  async function createNote(title = '无标题笔记') {
    try {
      const res = await fetch('/api/standalone-notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...auth.getHeaders() },
        body: JSON.stringify({ title }),
      })
      if (!res.ok) return null
      const note = await res.json()
      notes.value.unshift(note)
      _sortNotes()
      selectedNote.value = note
      return note
    } catch (e) {
      console.error('Failed to create note:', e)
      return null
    }
  }

  async function updateNote(id, data) {
    try {
      const res = await fetch(`/api/standalone-notes/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...auth.getHeaders() },
        body: JSON.stringify(data),
      })
      if (!res.ok) return null
      const updated = await res.json()
      const idx = notes.value.findIndex(n => n.id === id)
      if (idx !== -1) notes.value[idx] = updated
      if (selectedNote.value?.id === id) selectedNote.value = updated
      return updated
    } catch (e) {
      console.error('Failed to update note:', e)
      return null
    }
  }

  async function deleteNote(id) {
    try {
      const res = await fetch(`/api/standalone-notes/${id}`, {
        method: 'DELETE',
        headers: auth.getHeaders(),
      })
      if (!res.ok) return false
      notes.value = notes.value.filter(n => n.id !== id)
      if (selectedNote.value?.id === id) selectedNote.value = null
      return true
    } catch (e) {
      console.error('Failed to delete note:', e)
      return false
    }
  }

  async function uploadImage(file) {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('/api/standalone-notes/images', {
        method: 'POST',
        headers: auth.getHeaders(),
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '图片上传失败')
      }
      const data = await res.json()
      return data.url
    } catch (e) {
      console.error('Failed to upload image:', e)
      throw e
    }
  }

  async function selectNote(note) {
    if (hasUnsavedChanges.value && _saveCallback) {
      await _saveCallback()
    }
    selectedNote.value = note
  }

  function resetNotes() {
    notes.value = []
    selectedNote.value = null
  }

  async function loadTags() {
    try {
      const res = await fetch('/api/standalone-notes/tags', { headers: auth.getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { tags.value = []; return }
      tags.value = await res.json()
    } catch { tags.value = [] }
  }

  async function createTag(name, color = '#409eff') {
    try {
      const res = await fetch('/api/standalone-notes/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...auth.getHeaders() },
        body: JSON.stringify({ name, color }),
      })
      if (!res.ok) return null
      const tag = await res.json()
      tags.value.push(tag)
      return tag
    } catch (e) {
      console.error('Failed to create tag:', e)
      return null
    }
  }

  async function deleteTag(id) {
    try {
      const res = await fetch(`/api/standalone-notes/tags/${id}`, {
        method: 'DELETE',
        headers: auth.getHeaders(),
      })
      if (!res.ok) return false
      tags.value = tags.value.filter(t => t.id !== id)
      // 同时清除 notes 中该标签的引用
      for (const note of notes.value) {
        if (note.tags) note.tags = note.tags.filter(t => t.id !== id)
      }
      return true
    } catch (e) {
      console.error('Failed to delete tag:', e)
      return false
    }
  }

  function registerSaveCallback(fn) {
    _saveCallback = fn
  }

  function isDuplicateTitle(titleText, excludeId = null) {
    return notes.value.some(n =>
      n.title === titleText && n.id !== excludeId
    )
  }

  function _sortNotes() {
    const dir = sortOrder.value === 'asc' ? 1 : -1
    notes.value.sort((a, b) => {
      if (a.pinned !== b.pinned) return b.pinned ? 1 : -1
      if (sortMode.value === 'title') return dir * a.title.localeCompare(b.title)
      const key = sortMode.value === 'created' ? 'createdAt' : 'updatedAt'
      return dir * (a[key] || '').localeCompare(b[key] || '')
    })
  }

  async function togglePin(id) {
    const note = notes.value.find(n => n.id === id)
    if (!note) return
    const newPinned = !note.pinned
    try {
      const res = await fetch(`/api/standalone-notes/${id}/pin`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...auth.getHeaders() },
        body: JSON.stringify({ pinned: newPinned }),
      })
      if (!res.ok) return
      note.pinned = newPinned
      _sortNotes()
    } catch (e) {
      console.error('Failed to toggle pin:', e)
    }
  }

  function setSortMode(mode) {
    sortMode.value = mode
    _sortNotes()
  }

  function setSortOrder(order) {
    sortOrder.value = order
    _sortNotes()
  }

  function toggleSortOrder() {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
    _sortNotes()
  }

  return {
    notes, selectedNote, hasUnsavedChanges, sortMode, sortOrder, tags,
    loadNotes, createNote, updateNote, deleteNote, uploadImage,
    selectNote, resetNotes, registerSaveCallback, isDuplicateTitle,
    togglePin, setSortMode, setSortOrder, toggleSortOrder,
    loadTags, createTag, deleteTag,
  }
})

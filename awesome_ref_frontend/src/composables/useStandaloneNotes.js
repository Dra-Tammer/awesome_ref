import { ref } from 'vue'
import { useAuth } from './useAuth.js'

const notes = ref([])
const selectedNote = ref(null)

export function useStandaloneNotes() {
  const { getHeaders } = useAuth()

  async function loadNotes() {
    try {
      const res = await fetch('/api/standalone-notes', { headers: getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { notes.value = []; return }
      notes.value = await res.json()
    } catch { notes.value = [] }
  }

  async function createNote(title = '无标题笔记') {
    try {
      const res = await fetch('/api/standalone-notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify({ title }),
      })
      if (!res.ok) return null
      const note = await res.json()
      notes.value.unshift(note)
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
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
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
        headers: getHeaders(),
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
        headers: getHeaders(),
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

  function selectNote(note) {
    selectedNote.value = note
  }

  function resetNotes() {
    notes.value = []
    selectedNote.value = null
  }

  return { notes, selectedNote, loadNotes, createNote, updateNote, deleteNote, uploadImage, selectNote, resetNotes }
}

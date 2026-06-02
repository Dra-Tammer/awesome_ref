import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth.js'

export const useNotesStore = defineStore('notes', () => {
  const auth = useAuthStore()
  const notes = ref({})

  async function loadNotes() {
    try {
      const res = await fetch('/api/notes', { headers: auth.getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { notes.value = {}; return }
      notes.value = await res.json()
    } catch { notes.value = {} }
  }

  async function saveNote(refId, content) {
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...auth.getHeaders() },
        body: JSON.stringify({ refId, content }),
      })
      if (!res.ok) return null
      const data = await res.json()
      notes.value[refId] = data.note
      return data.note
    } catch (err) {
      console.error('Failed to save note:', err)
      return null
    }
  }

  function getNote(refId) { return notes.value[refId] || null }
  function hasNote(refId) { return !!(notes.value[refId]?.content) }
  function resetNotes() { notes.value = {} }

  async function uploadNoteImage(file) {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('/api/notes/images', {
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

  return { notes, loadNotes, saveNote, getNote, hasNote, resetNotes, uploadNoteImage }
})

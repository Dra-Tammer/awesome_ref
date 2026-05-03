import { ref } from 'vue'
import { useAuth } from './useAuth.js'

const notes = ref({})

export function useNotes() {
  const { getHeaders } = useAuth()

  async function loadNotes() {
    try {
      const res = await fetch('/api/notes', { headers: getHeaders() })
      if (res.status === 401) return
      if (!res.ok) { notes.value = {}; return }
      notes.value = await res.json()
    } catch { notes.value = {} }
  }

  async function saveNote(refId, content) {
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
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

  return { notes, loadNotes, saveNote, getNote, hasNote, resetNotes }
}

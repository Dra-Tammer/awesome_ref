<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import { useNotesStore } from '../stores/notes.js'
import { useReferencesStore } from '../stores/references.js'
import { useToastStore } from '../stores/toast.js'
import { highlightText } from '../utils/highlight.js'

const props = defineProps({
  refId: { type: String, required: true },
})

const notesStore = useNotesStore()
const refsStore = useReferencesStore()
const toastStore = useToastStore()

const content = ref('')
const editing = ref(false)
const saving = ref(false)
const saved = ref(false)
const updatedAt = ref('')
let saveTimer = null

onBeforeUnmount(() => { if (saveTimer) clearTimeout(saveTimer) })

watch(() => props.refId, (id) => {
  const note = notesStore.getNote(id)
  content.value = note?.content || ''
  updatedAt.value = note?.updatedAt || ''
  editing.value = false
  saved.value = false
}, { immediate: true })

function onEdit() {
  editing.value = true
}

async function onSave() {
  saving.value = true
  const note = await notesStore.saveNote(props.refId, content.value)
  if (note) {
    updatedAt.value = note.updatedAt
    saved.value = true
    editing.value = false
    toastStore.showToast('笔记已保存')
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => { saved.value = false }, 2000)
  } else {
    toastStore.showToast('保存失败', 'error')
  }
  saving.value = false
}

function onCancel() {
  const note = notesStore.getNote(props.refId)
  content.value = note?.content || ''
  editing.value = false
}

const formattedDate = computed(() => {
  if (!updatedAt.value) return ''
  const d = new Date(updatedAt.value)
  return d.toLocaleString('zh-CN')
})

const hasContent = computed(() => !!content.value.trim())
</script>

<template>
  <!-- 展示模式 -->
  <div v-if="!editing" class="note-card" :class="{ empty: !hasContent }">
    <div class="note-card-header">
      <span class="note-card-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        笔记
      </span>
      <div class="note-card-actions">
        <span v-if="saved" class="note-status saved">已保存</span>
        <span v-else-if="formattedDate" class="note-status">{{ formattedDate }}</span>
        <button class="btn-edit-note" @click="onEdit">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
          </svg>
          编辑
        </button>
      </div>
    </div>
    <div v-if="hasContent" class="note-card-text" v-html="highlightText(content, refsStore.searchQuery)"></div>
    <div v-else class="note-card-placeholder">点击编辑添加笔记...</div>
  </div>

  <!-- 编辑模式 -->
  <div v-else class="note-card editing">
    <div class="note-card-header">
      <span class="note-card-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        编辑笔记
      </span>
    </div>
    <textarea
      class="note-textarea"
      v-model="content"
      placeholder="为这篇文献添加笔记..."
    ></textarea>
    <div class="note-edit-actions">
      <button class="btn-cancel-note" @click="onCancel">取消</button>
      <button class="btn-save-note" @click="onSave" :disabled="saving">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </div>
  </div>
</template>

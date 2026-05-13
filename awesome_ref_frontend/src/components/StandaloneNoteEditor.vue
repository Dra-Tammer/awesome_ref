<script setup>
import { ref, watch, computed } from 'vue'
import { MdEditor, MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { useStandaloneNotes } from '../composables/useStandaloneNotes.js'
import { useTheme } from '../composables/useTheme.js'
import { useToast } from '../composables/useToast.js'

const { selectedNote, updateNote, uploadImage } = useStandaloneNotes()
const { theme } = useTheme()
const { showToast } = useToast()

const title = ref('')
const content = ref('')
const editing = ref(false)
const saving = ref(false)
const saved = ref(false)
let saveTimer = null
let lastNoteId = null

watch(selectedNote, (note, oldNote) => {
  const newId = note?.id ?? null
  // 同一篇笔记被更新（保存后触发），只同步数据，不重置编辑状态
  if (newId === lastNoteId && newId !== null) {
    if (note) {
      title.value = note.title || ''
      content.value = note.content || ''
    }
    return
  }
  // 切换到了不同的笔记，重置所有状态
  lastNoteId = newId
  if (note) {
    title.value = note.title || ''
    content.value = note.content || ''
  }
  editing.value = false
  saved.value = false
}, { immediate: true })

function onEdit() {
  editing.value = true
}

async function onSave() {
  if (!selectedNote.value) return
  saving.value = true
  const updated = await updateNote(selectedNote.value.id, {
    title: title.value,
    content: content.value,
  })
  if (updated) {
    saved.value = true
    editing.value = false
    showToast('笔记已保存')
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => { saved.value = false }, 2000)
  } else {
    showToast('保存失败', 'error')
  }
  saving.value = false
}

function onCancel() {
  if (selectedNote.value) {
    title.value = selectedNote.value.title || ''
    content.value = selectedNote.value.content || ''
  }
  editing.value = false
}

async function onUploadImg(files, callback) {
  const urls = await Promise.all(
    files.map(async (file) => {
      return await uploadImage(file)
    })
  )
  callback(urls)
}

const editorTheme = computed(() => theme.value === 'dark' ? 'dark' : 'light')
</script>

<template>
  <div v-if="!selectedNote" class="detail-panel">
    <div class="detail-empty">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.3">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
      <h2>笔记</h2>
      <p>选择一条笔记开始编辑</p>
    </div>
  </div>

  <div v-else class="detail-panel note-editor-panel">
    <div class="note-editor-header">
      <div class="note-editor-top">
        <input
          v-if="editing"
          class="note-title-input"
          v-model="title"
          placeholder="笔记标题..."
        />
        <h2 v-else class="note-title-display">{{ title || '无标题笔记' }}</h2>
        <div class="note-editor-actions">
          <span v-if="saved" class="note-status saved">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            已保存
          </span>
          <button v-if="!editing" class="btn-edit-note" @click="onEdit" title="编辑笔记">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <Transition name="note-mode" mode="out-in">
      <div v-if="!editing" key="preview" class="note-editor-preview" @click="onEdit">
        <MdPreview v-if="content" :modelValue="content" :theme="editorTheme" previewOnly />
        <div v-else class="note-editor-empty">点击开始编辑...</div>
      </div>

      <div v-else key="editor" class="note-editor-body">
        <MdEditor
          v-model="content"
          :theme="editorTheme"
          :onUploadImg="onUploadImg"
          :preview="false"
          :toolbarsExclude="['preview', 'previewOnly', 'htmlPreview']"
          style="height: 100%;"
        />
        <div class="note-edit-actions">
          <button class="btn-cancel-note" @click="onCancel">取消</button>
          <button class="btn-save-note" @click="onSave" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, nextTick } from 'vue'
import { MdEditor, MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { useStandaloneNotes } from '../composables/useStandaloneNotes.js'
import { useTheme } from '../composables/useTheme.js'
import { useToast } from '../composables/useToast.js'

const { selectedNote, updateNote, uploadImage, hasUnsavedChanges, registerSaveCallback } = useStandaloneNotes()
const { theme } = useTheme()
const { showToast } = useToast()

const title = ref('')
const content = ref('')
const editing = ref(false)
const saving = ref(false)
const saved = ref(false)
let saveTimer = null
let lastNoteId = null

// 守卫标志：selectedNote watch 同步数据时防止触发脏检测
let syncingFromNote = false

const wordCount = computed(() => {
  if (!content.value) return 0
  const text = content.value.replace(/[#*`~>\[\]()!|_\-]/g, '').trim()
  return text ? text.replace(/\s+/g, '').length : 0
})

const formattedUpdatedAt = computed(() => {
  if (!selectedNote.value?.updatedAt) return ''
  return new Date(selectedNote.value.updatedAt).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
})

// selectedNote 变化：区分同篇更新 vs 切换笔记
watch(selectedNote, (note) => {
  syncingFromNote = true
  const newId = note?.id ?? null
  if (newId === lastNoteId && newId !== null) {
    if (note) {
      title.value = note.title || ''
      content.value = note.content || ''
    }
    nextTick(() => { syncingFromNote = false })
    return
  }
  lastNoteId = newId
  if (note) {
    title.value = note.title || ''
    content.value = note.content || ''
  }
  editing.value = false
  saved.value = false
  hasUnsavedChanges.value = false
  nextTick(() => { syncingFromNote = false })
}, { immediate: true })

// 脏检测：标题或内容变化时标记未保存
watch([title, content], () => {
  if (syncingFromNote || !selectedNote.value) return
  hasUnsavedChanges.value =
    title.value !== (selectedNote.value.title || '') ||
    content.value !== (selectedNote.value.content || '')
})

function onEdit() {
  editing.value = true
}

// 仅在有变更时保存，返回 updated 或 null
async function saveIfDirty() {
  if (!selectedNote.value || !hasUnsavedChanges.value) return null
  saving.value = true
  const updated = await updateNote(selectedNote.value.id, {
    title: title.value,
    content: content.value,
  })
  if (updated) {
    hasUnsavedChanges.value = false
  }
  saving.value = false
  return updated
}

async function onSave() {
  const updated = await saveIfDirty()
  if (updated) {
    saved.value = true
    editing.value = false
    showToast('笔记已保存')
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => { saved.value = false }, 2000)
  } else if (selectedNote.value) {
    showToast('保存失败', 'error')
  }
}

function onCancel() {
  if (selectedNote.value) {
    title.value = selectedNote.value.title || ''
    content.value = selectedNote.value.content || ''
  }
  editing.value = false
}

// ── 图片上传 ──
async function onUploadImg(files, callback) {
  const urls = await Promise.all(
    files.map(async (file) => {
      return await uploadImage(file)
    })
  )
  callback(urls)
}

const editorTheme = computed(() => theme.value === 'dark' ? 'dark' : 'light')

function patchEditorBg() {
  setTimeout(() => {
    document.querySelectorAll('.note-editor-body .md-editor').forEach(el => {
      el.style.setProperty('background-color', 'transparent', 'important')
      el.style.setProperty('border', 'none', 'important')
      el.querySelectorAll('.md-editor-toolbar-wrapper, .md-editor-content, .md-editor-input-wrapper, .cm-editor, .cm-scroller, .cm-content, .cm-gutters').forEach(c => {
        c.style.setProperty('background-color', 'transparent', 'important')
      })
    })
  }, 50)
}
watch(editing, (v) => { if (v) patchEditorBg() })

// 注册自动保存回调
onMounted(() => {
  registerSaveCallback(async () => {
    await saveIfDirty()
  })
})
</script>

<template>
  <div v-if="!selectedNote" class="detail-panel note-editor-panel">
    <div class="detail-empty">
      <div class="note-empty-icon">
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.25">
          <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
        </svg>
      </div>
      <h2>开始书写</h2>
      <p>从左侧列表选择一篇笔记查看或编辑</p>
    </div>
  </div>

  <div v-else class="detail-panel note-editor-panel">
    <div class="note-editor-header">
      <div class="note-editor-top">
        <div class="note-editor-top-left">
          <h2 class="note-title-display">{{ title || '无标题笔记' }}</h2>
          <div v-if="!editing && (formattedUpdatedAt || wordCount)" class="note-editor-meta">
            <span v-if="formattedUpdatedAt" class="note-meta-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              修改于 {{ formattedUpdatedAt }}
            </span>
            <span class="note-meta-item note-meta-wordcount">{{ wordCount }} 字</span>
          </div>
        </div>
        <div class="note-editor-actions">
          <span v-if="saved" class="note-status saved">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            已保存
          </span>
          <button v-if="!editing" class="btn-edit-note" @click="onEdit" title="编辑笔记">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
            </svg>
            <span>编辑</span>
          </button>
        </div>
      </div>
    </div>

    <Transition name="note-mode" mode="out-in">
      <div v-if="!editing" key="preview" class="note-editor-preview">
        <MdPreview v-if="content" :modelValue="content" :theme="editorTheme" previewOnly />
        <div v-else class="note-editor-empty">点击编辑添加笔记...</div>
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

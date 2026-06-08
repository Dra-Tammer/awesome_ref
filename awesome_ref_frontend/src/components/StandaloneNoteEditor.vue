<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { MdEditor, MdPreview, config } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import hljs from 'highlight.js/lib/core'
import 'highlight.js/styles/atom-one-light.css'
import 'highlight.js/styles/atom-one-dark.css'

import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import java from 'highlight.js/lib/languages/java'
import cpp from 'highlight.js/lib/languages/cpp'
import csharp from 'highlight.js/lib/languages/csharp'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'
import markdown from 'highlight.js/lib/languages/markdown'
import yaml from 'highlight.js/lib/languages/yaml'
import shell from 'highlight.js/lib/languages/shell'
import php from 'highlight.js/lib/languages/php'
import ruby from 'highlight.js/lib/languages/ruby'
import swift from 'highlight.js/lib/languages/swift'
import kotlin from 'highlight.js/lib/languages/kotlin'
import dart from 'highlight.js/lib/languages/dart'
import lua from 'highlight.js/lib/languages/lua'
import r from 'highlight.js/lib/languages/r'
import matlab from 'highlight.js/lib/languages/matlab'
import dockerfile from 'highlight.js/lib/languages/dockerfile'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('java', java)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('csharp', csharp)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('shell', shell)
hljs.registerLanguage('php', php)
hljs.registerLanguage('ruby', ruby)
hljs.registerLanguage('swift', swift)
hljs.registerLanguage('kotlin', kotlin)
hljs.registerLanguage('dart', dart)
hljs.registerLanguage('lua', lua)
hljs.registerLanguage('r', r)
hljs.registerLanguage('matlab', matlab)
hljs.registerLanguage('dockerfile', dockerfile)

config({
  editorExtensions: {
    highlight: {
      instance: hljs
    }
  }
})
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import { useThemeStore } from '../stores/theme.js'
import { useToastStore } from '../stores/toast.js'

const standaloneNotesStore = useStandaloneNotesStore()
const themeStore = useThemeStore()
const toastStore = useToastStore()

const title = ref('')
const content = ref('')
const editing = ref(false)
const saving = ref(false)
const saved = ref(false)
let saveTimer = null
let lastNoteId = null

let syncingFromNote = false

const wordCount = computed(() => {
  if (!content.value) return 0
  const text = content.value.replace(/[#*`~>\[\]()!|_\-]/g, '').trim()
  return text ? text.replace(/\s+/g, '').length : 0
})

const formattedUpdatedAt = computed(() => {
  if (!standaloneNotesStore.selectedNote?.updatedAt) return ''
  return new Date(standaloneNotesStore.selectedNote.updatedAt).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
})

watch(() => standaloneNotesStore.selectedNote, (note) => {
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
  standaloneNotesStore.hasUnsavedChanges = false
  nextTick(() => { syncingFromNote = false })
}, { immediate: true })

watch([title, content], () => {
  if (syncingFromNote || !standaloneNotesStore.selectedNote) return
  standaloneNotesStore.hasUnsavedChanges =
    title.value !== (standaloneNotesStore.selectedNote.title || '') ||
    content.value !== (standaloneNotesStore.selectedNote.content || '')
})

// 自动保存（3 秒防抖）
let autoSaveTimer = null
watch(content, () => {
  if (syncingFromNote || !standaloneNotesStore.selectedNote || !editing.value) return
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(async () => {
    if (standaloneNotesStore.hasUnsavedChanges) {
      const result = await saveIfDirty()
      if (result === 'saved') {
        saved.value = true
        if (saveTimer) clearTimeout(saveTimer)
        saveTimer = setTimeout(() => { saved.value = false }, 2000)
      }
    }
  }, 3000)
})

// 关闭标签页前提醒未保存内容
function onBeforeUnload(e) {
  if (standaloneNotesStore.hasUnsavedChanges) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', onBeforeUnload)
  standaloneNotesStore.registerSaveCallback(async () => {
    await saveIfDirty()
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  if (saveTimer) clearTimeout(saveTimer)
})

function onEdit() {
  editing.value = true
}

async function saveIfDirty() {
  if (!standaloneNotesStore.selectedNote || !standaloneNotesStore.hasUnsavedChanges) return 'nochange'
  saving.value = true
  const updated = await standaloneNotesStore.updateNote(standaloneNotesStore.selectedNote.id, {
    title: title.value,
    content: content.value,
  })
  saving.value = false
  if (updated) {
    standaloneNotesStore.hasUnsavedChanges = false
    return 'saved'
  }
  return 'failed'
}

async function onSave() {
  const result = await saveIfDirty()
  if (result === 'saved') {
    saved.value = true
    editing.value = false
    toastStore.showToast('笔记已保存')
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => { saved.value = false }, 2000)
  } else if (result === 'nochange') {
    editing.value = false
    saved.value = true
    toastStore.showToast('已是最新')
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => { saved.value = false }, 2000)
  } else if (result === 'failed') {
    toastStore.showToast('保存失败', 'error')
  }
}

function onCancel() {
  if (standaloneNotesStore.selectedNote) {
    title.value = standaloneNotesStore.selectedNote.title || ''
    content.value = standaloneNotesStore.selectedNote.content || ''
  }
  editing.value = false
}

async function onUploadImg(files, callback) {
  const results = await Promise.allSettled(
    files.map(async (file) => {
      return await standaloneNotesStore.uploadImage(file)
    })
  )
  const urls = results.filter(r => r.status === 'fulfilled').map(r => r.value)
  const failed = results.filter(r => r.status === 'rejected')
  if (failed.length > 0) {
    toastStore.showToast(`${failed.length} 张图片上传失败`, 'error')
  }
  callback(urls)
}

const editorTheme = computed(() => themeStore.theme === 'dark' ? 'dark' : 'light')

// 标签切换（类似文献分组）
function isNoteInTag(tagId) {
  const note = standaloneNotesStore.selectedNote
  return note?.tags?.some(t => t.id === tagId) || false
}

async function toggleNoteTag(tagId) {
  const note = standaloneNotesStore.selectedNote
  if (!note) return
  const currentIds = (note.tags || []).map(t => t.id)
  const newIds = currentIds.includes(tagId)
    ? currentIds.filter(id => id !== tagId)
    : [...currentIds, tagId]
  await standaloneNotesStore.updateNote(note.id, { tags: newIds })
}

</script>

<template>
  <div v-if="!standaloneNotesStore.selectedNote" class="detail-panel note-editor-panel">
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
    <Transition name="note-mode" mode="out-in">
      <div v-if="!editing" key="preview" class="note-editor-preview">
        <div class="note-editor-header">
          <div class="note-editor-top">
            <div class="note-editor-top-left">
              <h2 class="note-title-display">{{ title || '无标题笔记' }}</h2>
              <div v-if="formattedUpdatedAt || wordCount" class="note-editor-meta">
                <span v-if="formattedUpdatedAt" class="note-meta-item">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                  修改于 {{ formattedUpdatedAt }}
                </span>
                <span class="note-meta-item note-meta-wordcount">{{ wordCount }} 字</span>
              </div>
              <!-- 标签选择（类似文献分组） -->
              <div v-if="standaloneNotesStore.tags.length" class="note-tag-chips">
                <span
                  v-for="tag in standaloneNotesStore.tags"
                  :key="tag.id"
                  class="note-tag-chip-selectable"
                  :class="{ active: isNoteInTag(tag.id) }"
                  :style="isNoteInTag(tag.id) ? { background: tag.color + '20', borderColor: tag.color, color: tag.color } : {}"
                  @click="toggleNoteTag(tag.id)"
                >
                  <span class="tag-color-dot" :style="{ background: isNoteInTag(tag.id) ? tag.color : 'var(--text-secondary)' }"></span>
                  {{ tag.name }}
                </span>
              </div>
            </div>
            <div class="note-editor-actions">
              <span v-if="saved" class="note-status saved">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                已保存
              </span>
              <button class="btn-edit-note" @click="onEdit" title="编辑笔记">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
                </svg>
                <span>编辑</span>
              </button>
            </div>
          </div>
        </div>
        <MdPreview v-if="content" :modelValue="content" :theme="editorTheme" previewOnly />
        <div v-else class="note-editor-empty">点击编辑添加笔记...</div>
      </div>

      <div v-else key="editor" class="note-editor-body">
        <!-- 编辑模式下也显示标签选择 -->
        <div v-if="standaloneNotesStore.tags.length" class="note-tag-chips note-tag-chips-editor">
          <span
            v-for="tag in standaloneNotesStore.tags"
            :key="tag.id"
            class="note-tag-chip-selectable"
            :class="{ active: isNoteInTag(tag.id) }"
            :style="isNoteInTag(tag.id) ? { background: tag.color + '20', borderColor: tag.color, color: tag.color } : {}"
            @click="toggleNoteTag(tag.id)"
          >
            <span class="tag-color-dot" :style="{ background: isNoteInTag(tag.id) ? tag.color : 'var(--text-secondary)' }"></span>
            {{ tag.name }}
          </span>
        </div>
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

<style scoped>
.note-editor-body :deep(.md-editor),
.note-editor-body :deep(.md-editor-toolbar-wrapper),
.note-editor-body :deep(.md-editor-content),
.note-editor-body :deep(.md-editor-input-wrapper),
.note-editor-body :deep(.cm-editor),
.note-editor-body :deep(.cm-scroller),
.note-editor-body :deep(.cm-content),
.note-editor-body :deep(.cm-gutters) {
  background-color: transparent !important;
}
.note-editor-body :deep(.md-editor) {
  border: none !important;
}
</style>

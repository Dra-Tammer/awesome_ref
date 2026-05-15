<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useStandaloneNotes } from '../composables/useStandaloneNotes.js'
import { useToast } from '../composables/useToast.js'
import ConfirmDialog from './ConfirmDialog.vue'

const { notes, selectedNote, createNote, deleteNote, selectNote, updateNote, isDuplicateTitle } = useStandaloneNotes()
const { showToast } = useToast()

const searchQuery = ref('')
const deleteTarget = ref(null)
const showTitleModal = ref(false)
const newNoteTitle = ref('')
const titleInputRef = ref(null)

// 重命名状态
const renameTarget = ref(null)
const renameTitle = ref('')
const renameInputRef = ref(null)
function setRenameRef(el) { renameInputRef.value = el }

watch(showTitleModal, (v) => {
  if (v) nextTick(() => titleInputRef.value?.focus())
})

const filteredNotes = computed(() => {
  if (!searchQuery.value.trim()) return notes.value
  const q = searchQuery.value.toLowerCase()
  return notes.value.filter(n =>
    n.title.toLowerCase().includes(q) || n.content.toLowerCase().includes(q)
  )
})

function getContentPreview(content) {
  if (!content) return ''
  const text = content.replace(/[#*`~>\[\]()!|_\-]/g, '').replace(/\n+/g, ' ').trim()
  return text.length > 60 ? text.slice(0, 60) + '...' : text
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function onCreateNote() {
  newNoteTitle.value = ''
  showTitleModal.value = true
}

async function onConfirmCreate() {
  const title = newNoteTitle.value.trim() || '无标题笔记'
  if (isDuplicateTitle(title)) {
    showToast('已存在同名笔记', 'error')
    return
  }
  showTitleModal.value = false
  const note = await createNote(title)
  if (note) showToast('笔记已创建')
}

function onClickNote(note) {
  selectNote(note)
}

async function onConfirmDelete() {
  if (!deleteTarget.value) return
  const ok = await deleteNote(deleteTarget.value.id)
  if (ok) showToast('笔记已删除')
  deleteTarget.value = null
}

function startRename(note) {
  renameTarget.value = note.id
  renameTitle.value = note.title
  nextTick(() => {
    renameInputRef.value?.focus()
    renameInputRef.value?.select()
  })
}

async function confirmRename() {
  const id = renameTarget.value
  if (!id) return
  const newTitle = renameTitle.value.trim()
  const original = notes.value.find(n => n.id === id)
  renameTarget.value = null
  if (!newTitle || newTitle === original?.title) return
  if (isDuplicateTitle(newTitle, id)) {
    showToast('已存在同名笔记', 'error')
    return
  }
  const updated = await updateNote(id, { title: newTitle })
  if (updated) {
    showToast('标题已重命名')
  } else {
    showToast('重命名失败', 'error')
  }
}

function cancelRename() {
  renameTarget.value = null
}

// 点击外部自动退出重命名
function onDocumentClick(e) {
  if (!renameTarget.value) return
  if (!e.target.closest('.note-list-card-rename')) {
    confirmRename()
  }
}
onMounted(() => document.addEventListener('mousedown', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocumentClick))
</script>

<template>
  <div class="note-list-panel">
    <div class="list-header">
      <span class="list-title">笔记</span>
      <div class="list-header-right">
        <button class="btn-sort" @click="onCreateNote" title="新建笔记">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
        <span class="ref-count">{{ notes.length }} 篇</span>
      </div>
    </div>
    <div class="list-search">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" placeholder="搜索笔记..." v-model="searchQuery">
      <button v-if="searchQuery" class="btn-search-clear" @click="searchQuery = ''" title="清空搜索">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <div class="ref-list">
      <div v-if="notes.length === 0" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <p>点击上方 + 按钮<br>创建你的第一条笔记</p>
      </div>
      <div v-else-if="filteredNotes.length === 0" class="empty-state">
        <p>没有匹配的笔记</p>
      </div>
      <template v-else>
        <div
          v-for="note in filteredNotes"
          :key="note.id"
          class="note-list-card"
          :class="{ active: selectedNote?.id === note.id }"
          @click="onClickNote(note)"
        >
          <div v-if="renameTarget === note.id" class="note-list-card-rename" @click.stop>
            <input
              :ref="setRenameRef"
              class="note-list-rename-input"
              v-model="renameTitle"
              @keydown.enter.prevent="confirmRename"
              @keydown.escape="cancelRename"
              @blur="confirmRename"
            />
          </div>
          <template v-else>
            <div class="note-list-card-title">{{ note.title || '无标题笔记' }}</div>
            <div v-if="getContentPreview(note.content)" class="note-list-card-preview">{{ getContentPreview(note.content) }}</div>
          </template>
          <div class="note-list-card-row">
            <span class="note-list-card-date">{{ formatDate(note.updatedAt) }}</span>
            <div class="note-list-card-actions">
              <button class="btn-note-action" @click.stop="startRename(note)" title="重命名">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
                </svg>
              </button>
              <button class="btn-note-action btn-note-delete" @click.stop="deleteTarget = note" title="删除笔记">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <ConfirmDialog
      :visible="!!deleteTarget"
      title="删除笔记"
      :message="`确定删除「${deleteTarget?.title || '无标题笔记'}」吗？`"
      @confirm="onConfirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>

  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showTitleModal" class="note-title-overlay" @click.self="showTitleModal = false">
        <div class="note-title-modal">
          <div class="note-title-modal-header">
            <div class="note-title-modal-header-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/><line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/>
              </svg>
              <span>新建笔记</span>
            </div>
            <button class="note-title-modal-close" @click="showTitleModal = false">&times;</button>
          </div>
          <form class="note-title-modal-body" @submit.prevent="onConfirmCreate">
            <input
              ref="titleInputRef"
              type="text"
              v-model="newNoteTitle"
              placeholder="输入笔记标题（可留空）"
              @keydown.enter.prevent="onConfirmCreate"
            />
            <div class="note-title-modal-actions">
              <button type="button" class="btn-note-title-cancel" @click="showTitleModal = false">取消</button>
              <button type="submit" class="btn-note-title-confirm">创建</button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import { useToastStore } from '../stores/toast.js'
import ConfirmDialog from './ConfirmDialog.vue'

const standaloneNotesStore = useStandaloneNotesStore()
const toastStore = useToastStore()

const searchQuery = ref('')
const deleteTarget = ref(null)
const showTitleModal = ref(false)
const newNoteTitle = ref('')
const titleInputRef = ref(null)

const renameTarget = ref(null)
const renameTitle = ref('')
const renameInputRef = ref(null)
function setRenameRef(el) { renameInputRef.value = el }

const showSortMenu = ref(false)
const sortMenuRef = ref(null)
const sortLabel = { updated: '更新时间', created: '创建时间', title: '标题' }

// 标签筛选
const selectedTagIds = ref(new Set())

// 标签管理弹窗
const showTagManager = ref(false)
const newTagName = ref('')
const newTagColor = ref('#409eff')
const TAG_COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9b59b6', '#1abc9c', '#e91e63']

// 笔记标签选择器
const tagPickerNoteId = ref(null)
const tagPickerRef = ref(null)

function onSortMenuClickOutside(e) {
  if (sortMenuRef.value && !sortMenuRef.value.contains(e.target)) {
    showSortMenu.value = false
  }
}

function onTagPickerClickOutside(e) {
  if (tagPickerRef.value && !tagPickerRef.value.contains(e.target)) {
    tagPickerNoteId.value = null
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onSortMenuClickOutside)
  document.addEventListener('mousedown', onTagPickerClickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onSortMenuClickOutside)
  document.removeEventListener('mousedown', onTagPickerClickOutside)
})

watch(showTitleModal, (v) => {
  if (v) nextTick(() => titleInputRef.value?.focus())
})

// 搜索增强：标签名匹配 + 内容上下文片段
const filteredNotes = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const hasTagFilter = selectedTagIds.value.size > 0

  let result = standaloneNotesStore.notes

  // 标签筛选（交集）
  if (hasTagFilter) {
    result = result.filter(n =>
      n.tags && [...selectedTagIds.value].every(tid => n.tags.some(t => t.id === tid))
    )
  }

  // 文本搜索（标题 + 内容 + 标签名）
  if (q) {
    const words = q.split(/\s+/)
    result = result.filter(n => {
      const tagNames = (n.tags || []).map(t => t.name.toLowerCase()).join(' ')
      const fields = [n.title?.toLowerCase() || '', n.content?.toLowerCase() || '', tagNames]
      return words.every(w => fields.some(f => f.includes(w)))
    })
  }

  return result
})

// 搜索高亮：返回带 <mark> 的 HTML
function highlightText(text, query) {
  if (!query?.trim() || !text) return escapeHtml(text || '')
  const words = query.trim().toLowerCase().split(/\s+/)
  let result = escapeHtml(text)
  for (const word of words) {
    if (!word) continue
    const regex = new RegExp(`(${escapeRegex(word)})`, 'gi')
    result = result.replace(regex, '<mark class="search-highlight">$1</mark>')
  }
  return result
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// 内容预览：搜索时展示匹配片段，否则截取开头
function getContentPreview(content, query) {
  if (!content) return ''
  const text = content.replace(/[#*`~>\[\]()!|_\-]/g, '').replace(/\n+/g, ' ').trim()
  const q = query?.trim().toLowerCase()
  if (q) {
    const lower = text.toLowerCase()
    const idx = lower.indexOf(q.split(/\s+/)[0])
    if (idx > -1) {
      const start = Math.max(0, idx - 15)
      const end = Math.min(text.length, idx + 50)
      const snippet = (start > 0 ? '...' : '') + text.slice(start, end) + (end < text.length ? '...' : '')
      return snippet
    }
  }
  return text.length > 60 ? text.slice(0, 60) + '...' : text
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function onCreateNote() {
  newNoteTitle.value = ''
  showTitleModal.value = true
}

async function onConfirmCreate() {
  const title = newNoteTitle.value.trim() || '无标题笔记'
  if (standaloneNotesStore.isDuplicateTitle(title)) {
    toastStore.showToast('已存在同名笔记', 'error')
    return
  }
  showTitleModal.value = false
  const note = await standaloneNotesStore.createNote(title)
  if (note) toastStore.showToast('笔记已创建')
}

function onClickNote(note) {
  standaloneNotesStore.selectNote(note)
}

async function onConfirmDelete() {
  if (!deleteTarget.value) return
  const ok = await standaloneNotesStore.deleteNote(deleteTarget.value.id)
  if (ok) toastStore.showToast('笔记已删除')
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
  const original = standaloneNotesStore.notes.find(n => n.id === id)
  renameTarget.value = null
  if (!newTitle || newTitle === original?.title) return
  if (standaloneNotesStore.isDuplicateTitle(newTitle, id)) {
    toastStore.showToast('已存在同名笔记', 'error')
    return
  }
  const updated = await standaloneNotesStore.updateNote(id, { title: newTitle })
  if (updated) {
    toastStore.showToast('标题已重命名')
  } else {
    toastStore.showToast('重命名失败', 'error')
  }
}

function cancelRename() {
  renameTarget.value = null
}

function onDocumentClick(e) {
  if (!renameTarget.value) return
  if (!e.target.closest('.note-list-card-rename')) {
    confirmRename()
  }
}
onMounted(() => document.addEventListener('mousedown', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocumentClick))

// 标签筛选
function toggleTagFilter(tagId) {
  const s = new Set(selectedTagIds.value)
  if (s.has(tagId)) s.delete(tagId)
  else s.add(tagId)
  selectedTagIds.value = s
}

function clearTagFilter() {
  selectedTagIds.value = new Set()
}

// 标签管理
async function onCreateTag() {
  const name = newTagName.value.trim()
  if (!name) return
  const tag = await standaloneNotesStore.createTag(name, newTagColor.value)
  if (tag) {
    toastStore.showToast(`标签「${name}」已创建`)
    newTagName.value = ''
  } else {
    toastStore.showToast('创建失败，可能已存在同名标签', 'error')
  }
}

async function onDeleteTag(tagId) {
  const ok = await standaloneNotesStore.deleteTag(tagId)
  if (ok) toastStore.showToast('标签已删除')
}

// 笔记标签选择器
function toggleTagPicker(noteId, e) {
  e?.stopPropagation()
  tagPickerNoteId.value = tagPickerNoteId.value === noteId ? null : noteId
}

async function toggleNoteTag(note, tagId) {
  const currentIds = (note.tags || []).map(t => t.id)
  let newIds
  if (currentIds.includes(tagId)) {
    newIds = currentIds.filter(id => id !== tagId)
  } else {
    newIds = [...currentIds, tagId]
  }
  await standaloneNotesStore.updateNote(note.id, { tags: newIds })
}
</script>

<template>
  <div class="note-list-panel">
    <!-- 头部：标题 + 操作按钮 -->
    <div class="list-header">
      <span class="list-title">笔记</span>
      <div class="list-header-right">
        <div class="sort-menu-wrapper" ref="sortMenuRef">
          <button class="btn-icon" @click="showSortMenu = !showSortMenu" :title="'排序: ' + sortLabel[standaloneNotesStore.sortMode]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="4" y1="6" x2="16" y2="6"/><line x1="4" y1="12" x2="13" y2="12"/><line x1="4" y1="18" x2="10" y2="18"/>
            </svg>
          </button>
          <Transition name="dropdown">
            <div v-if="showSortMenu" class="sort-dropdown">
              <button class="sort-dropdown-item" :class="{ active: standaloneNotesStore.sortMode === 'updated' }" @click="standaloneNotesStore.setSortMode('updated'); showSortMenu = false">更新时间</button>
              <button class="sort-dropdown-item" :class="{ active: standaloneNotesStore.sortMode === 'created' }" @click="standaloneNotesStore.setSortMode('created'); showSortMenu = false">创建时间</button>
              <button class="sort-dropdown-item" :class="{ active: standaloneNotesStore.sortMode === 'title' }" @click="standaloneNotesStore.setSortMode('title'); showSortMenu = false">标题</button>
            </div>
          </Transition>
        </div>
        <button class="btn-icon" @click="standaloneNotesStore.toggleSortOrder()" :title="standaloneNotesStore.sortOrder === 'desc' ? '当前：降序，点击切换' : '当前：升序，点击切换'">
          <svg v-if="standaloneNotesStore.sortOrder === 'desc'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="18 15 12 9 6 15"/>
          </svg>
        </button>
        <button class="btn-icon" @click="showTagManager = true" title="管理标签">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>
          </svg>
        </button>
        <button class="btn-icon btn-icon-accent" @click="onCreateNote" title="新建笔记">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
        <span class="note-count">{{ standaloneNotesStore.notes.length }}</span>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="list-search">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" placeholder="搜索标题、内容、标签..." v-model="searchQuery">
      <button v-if="searchQuery" class="btn-search-clear" @click="searchQuery = ''">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- 标签筛选栏 -->
    <div v-if="standaloneNotesStore.tags.length" class="note-tag-filter-bar">
      <span
        v-for="tag in standaloneNotesStore.tags"
        :key="tag.id"
        class="note-tag-filter-chip"
        :class="{ active: selectedTagIds.has(tag.id) }"
        @click="toggleTagFilter(tag.id)"
      >
        <span class="tag-color-dot" :style="{ background: tag.color }"></span>
        {{ tag.name }}
      </span>
      <span v-if="selectedTagIds.size > 0" class="note-tag-filter-chip" @click="clearTagFilter" style="opacity: 0.6;">
        清除
      </span>
    </div>

    <!-- 笔记列表 -->
    <div class="ref-list">
      <div v-if="standaloneNotesStore.notes.length === 0" class="empty-state">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <p>点击 + 创建第一条笔记</p>
      </div>
      <div v-else-if="filteredNotes.length === 0" class="empty-state">
        <p>没有匹配的笔记</p>
      </div>
      <template v-else>
        <div
          v-for="note in filteredNotes"
          :key="note.id"
          class="note-list-card"
          :class="{ active: standaloneNotesStore.selectedNote?.id === note.id, pinned: note.pinned }"
          @click="onClickNote(note)"
        >
          <!-- 重命名模式 -->
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
            <!-- 第一行：标题 + 置顶标识 + 日期 -->
            <div class="note-card-row-title">
              <span v-if="note.pinned" class="pin-dot" title="已置顶"></span>
              <span class="note-list-card-title" v-if="searchQuery.trim()" v-html="highlightText(note.title || '无标题笔记', searchQuery)"></span>
              <span v-else class="note-list-card-title">{{ note.title || '无标题笔记' }}</span>
              <span class="note-list-card-date">{{ formatDate(note.updatedAt) }}</span>
            </div>
            <!-- 第二行：内容预览 -->
            <div v-if="getContentPreview(note.content, searchQuery)" class="note-list-card-preview">
              <span v-if="searchQuery.trim()" v-html="highlightText(getContentPreview(note.content, searchQuery), searchQuery)"></span>
              <span v-else>{{ getContentPreview(note.content, searchQuery) }}</span>
            </div>
          </template>

          <!-- 悬浮操作按钮（hover 显示） -->
          <div class="note-card-hover-actions" @click.stop>
            <button class="btn-note-action" @click="startRename(note)" title="重命名">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
              </svg>
            </button>
            <button class="btn-note-action" :class="{ 'btn-note-pinned': note.pinned }" @click="standaloneNotesStore.togglePin(note.id)" :title="note.pinned ? '取消置顶' : '置顶'">
              <svg width="11" height="11" viewBox="0 0 24 24" :fill="note.pinned ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                <path d="M12 2L15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2z"/>
              </svg>
            </button>
            <button class="btn-note-action btn-note-delete" @click="deleteTarget = note" title="删除">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
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

  <!-- 新建笔记弹窗 -->
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

  <!-- 标签管理弹窗 -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showTagManager" class="tag-manager-overlay" @click.self="showTagManager = false">
        <div class="tag-manager-modal">
          <div class="tag-manager-header">
            <div class="tag-manager-header-left">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2">
                <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>
              </svg>
              <span>管理标签</span>
            </div>
            <button class="tag-manager-close" @click="showTagManager = false">&times;</button>
          </div>
          <div class="tag-manager-body">
            <div v-if="standaloneNotesStore.tags.length === 0" class="tag-manager-empty">
              暂无标签，在下方创建
            </div>
            <div v-else class="tag-manager-list">
              <div v-for="tag in standaloneNotesStore.tags" :key="tag.id" class="tag-manager-item">
                <div class="tag-manager-item-left">
                  <span class="tag-color-dot" :style="{ background: tag.color }"></span>
                  <span class="tag-manager-item-name">{{ tag.name }}</span>
                  <span class="tag-manager-item-count">
                    {{ standaloneNotesStore.notes.filter(n => (n.tags || []).some(t => t.id === tag.id)).length }}
                  </span>
                </div>
                <button class="tag-manager-item-delete" @click="onDeleteTag(tag.id)" title="删除标签">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <form class="tag-manager-create" @submit.prevent="onCreateTag">
            <div class="tag-manager-create-row">
              <input
                type="text"
                v-model="newTagName"
                placeholder="标签名称"
                maxlength="50"
              />
              <button type="submit" class="tag-manager-create-btn" :disabled="!newTagName.trim()">创建</button>
            </div>
            <div class="tag-manager-color-palette">
              <span
                v-for="color in TAG_COLORS"
                :key="color"
                class="tag-color-option"
                :class="{ active: newTagColor === color }"
                :style="{ background: color }"
                @click="newTagColor = color"
              ></span>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

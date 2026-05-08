<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useReferences } from '../composables/useReferences.js'
import { useNotes } from '../composables/useNotes.js'
import { useToast } from '../composables/useToast.js'
import { highlightText } from '../utils/highlight.js'
import ConfirmDialog from './ConfirmDialog.vue'

const { filteredReferences, references, trashReferences, selectByIndex, selectById, selectedReference, sortField, sortOrder, toggleSort, setSortField, searchQuery, activeGroupId, isTrashMode, clearTrash } = useReferences()
const { hasNote } = useNotes()
const { showToast } = useToast()

const listRef = ref(null)
const clearTrashConfirm = ref(false)
const showSortMenu = ref(false)
const sortMenuRef = ref(null)

const sortFieldLabel = computed(() => {
  const map = { year: '年份', created: '添加时间', note: '笔记时间' }
  return map[sortField.value] || '年份'
})

function onSortFieldClick(e) {
  e.stopPropagation()
  showSortMenu.value = !showSortMenu.value
}

function onPickField(field) {
  setSortField(field)
  showSortMenu.value = false
}

function onClickOutside(e) {
  if (sortMenuRef.value && !sortMenuRef.value.contains(e.target)) {
    showSortMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))

function scrollToActive() {
  if (!listRef.value) return
  const el = listRef.value.querySelector('.ref-card.active')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

function getAuthorDisplay(authors) {
  if (authors.length === 0) return '未知作者'
  const first = authors[0].split(',')[0]
  return authors.length > 1 ? `${first} 等` : first
}

function onClickRef(ref) {
  selectById(ref.id)
}

async function onConfirmClearTrash() {
  clearTrashConfirm.value = false
  const count = await clearTrash()
  if (count > 0) showToast(`已清空 ${count} 篇文献，无法撤回`, 'error')
}
</script>

<template>
  <div class="list-header">
    <span class="list-title">{{ isTrashMode ? '回收站' : '文献列表' }}</span>
    <div class="list-header-right" v-if="!isTrashMode">
      <!-- sort direction toggle -->
      <button class="btn-sort" @click="toggleSort" :title="sortOrder === 'desc' ? '降序' : '升序'">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <polyline v-if="sortOrder === 'desc'" points="19 12 12 19 5 12"/>
          <polyline v-else points="5 12 12 5 19 12"/>
        </svg>
      </button>
      <!-- sort field selector -->
      <div class="sort-menu-wrapper" ref="sortMenuRef">
        <button class="btn-sort btn-sort-field" @click="onSortFieldClick" title="排序字段">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>
          </svg>
          <span class="btn-sort-label">{{ sortFieldLabel }}</span>
        </button>
        <Transition name="dropdown">
          <div v-if="showSortMenu" class="sort-dropdown">
            <button class="sort-dropdown-item" :class="{ active: sortField === 'year' }" @click="onPickField('year')">文献年份</button>
            <button class="sort-dropdown-item" :class="{ active: sortField === 'created' }" @click="onPickField('created')">添加时间</button>
            <button class="sort-dropdown-item" :class="{ active: sortField === 'note' }" @click="onPickField('note')">笔记更新时间</button>
          </div>
        </Transition>
      </div>
      <button class="btn-sort" @click="scrollToActive" title="定位到当前文献">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/>
          <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
          <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
        </svg>
      </button>
      <span class="ref-count">{{ filteredReferences.length }} 篇</span>
    </div>
    <div class="list-header-right" v-else>
      <button v-if="trashReferences.length > 0" class="btn-sort btn-clear-trash" @click="clearTrashConfirm = true" title="清空回收站">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>
        </svg>
      </button>
      <span class="ref-count trash-hint">{{ filteredReferences.length }} 篇 · 30天后自动清除</span>
    </div>
  </div>
  <div class="list-search">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
    <input type="text" placeholder="搜索标题、摘要、作者、笔记..." v-model="searchQuery">
    <button v-if="searchQuery" class="btn-search-clear" @click="searchQuery = ''" title="清空搜索">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </div>
  <div class="ref-list" ref="listRef">
    <div v-if="references.length === 0 && !isTrashMode" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <p>拖拽 .ris 文件到此处<br>或点击上方"导入 RIS"按钮</p>
    </div>
    <div v-else-if="isTrashMode && trashReferences && trashReferences.length === 0" class="empty-state">
      <p>回收站为空</p>
    </div>
    <div v-else-if="filteredReferences.length === 0" class="empty-state">
      <p>当前分组没有文献</p>
    </div>
    <template v-else>
      <div
        v-for="ref in filteredReferences"
        :key="ref.id"
        class="ref-card"
        :class="{ active: selectedReference?.id === ref.id }"
        @click="onClickRef(ref)"
      >
        <div class="ref-card-main">
          <div class="ref-card-title" v-html="highlightText(ref.title || '无标题', searchQuery)"></div>
          <div class="ref-card-meta">
            <span class="ref-card-authors" v-html="highlightText(getAuthorDisplay(ref.authors), searchQuery)"></span>
            <span v-if="ref.year" class="ref-card-year">{{ ref.year }}</span>
            <span v-if="ref.journal" class="ref-card-journal">{{ ref.journal }}</span>
          </div>
        </div>
        <span v-if="hasNote(ref.id)" class="ref-card-note-badge" title="有笔记"></span>
      </div>
    </template>
  </div>

  <ConfirmDialog
    :visible="clearTrashConfirm"
    title="清空回收站"
    :message="`确定清空回收站中的全部 ${trashReferences.length} 篇文献吗？此操作不可撤销。`"
    @confirm="onConfirmClearTrash"
    @cancel="clearTrashConfirm = false"
  />
</template>

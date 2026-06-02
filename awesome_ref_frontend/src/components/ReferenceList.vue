<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useReferencesStore } from '../stores/references.js'
import { useNotesStore } from '../stores/notes.js'
import { useGroupsStore } from '../stores/groups.js'
import { useAuthStore } from '../stores/auth.js'
import { useToastStore } from '../stores/toast.js'
import { highlightText } from '../utils/highlight.js'
import ConfirmDialog from './ConfirmDialog.vue'
import ReferenceEditor from './ReferenceEditor.vue'

const refsStore = useReferencesStore()
const notesStore = useNotesStore()
const groupsStore = useGroupsStore()
const auth = useAuthStore()
const toastStore = useToastStore()

const listRef = ref(null)
const clearTrashConfirm = ref(false)
const showSortMenu = ref(false)
const sortMenuRef = ref(null)

const sortFieldLabel = computed(() => {
  const map = { year: '年份', created: '添加时间', note: '笔记时间' }
  return map[refsStore.sortField] || '年份'
})

function onSortFieldClick(e) {
  e.stopPropagation()
  showAddMenu.value = false
  showSortMenu.value = !showSortMenu.value
}

function onPickField(field) {
  refsStore.setSortField(field)
  showSortMenu.value = false
}

function onClickOutside(e) {
  if (sortMenuRef.value && !sortMenuRef.value.contains(e.target)) {
    showSortMenu.value = false
  }
  if (addMenuRef.value && !addMenuRef.value.contains(e.target)) {
    showAddMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))

function scrollToActive() {
  if (!listRef.value) return
  const el = listRef.value.querySelector('.ref-card.active')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

watch(() => refsStore.selectedReference, () => {
  nextTick(() => scrollToActive())
})

function getAuthorDisplay(authors) {
  if (authors.length === 0) return '未知作者'
  const first = authors[0].split(',')[0]
  return authors.length > 1 ? `${first} 等` : first
}

function onClickRef(ref) {
  refsStore.selectById(ref.id)
}

async function onConfirmClearTrash() {
  clearTrashConfirm.value = false
  const count = await refsStore.clearTrash()
  if (count > 0) toastStore.showToast(`已清空 ${count} 篇文献，无法撤回`, 'error')
}

// ── 新建 / 导入文献 ──
const showNewRefModal = ref(false)
const showImportModal = ref(false)
const showAddMenu = ref(false)
const addMenuRef = ref(null)

function toggleAddMenu(e) {
  e.stopPropagation()
  showSortMenu.value = false
  showAddMenu.value = !showAddMenu.value
}

function onNewRef() {
  showAddMenu.value = false
  showNewRefModal.value = true
}

function onImportRIS() {
  showImportModal.value = false
  showAddMenu.value = false
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.ris,.txt'
  input.multiple = true
  input.onchange = async (e) => {
    const files = Array.from(e.target.files)
    const { parseRIS } = await import('../utils/risParser.js')
    const risFiles = files.filter(f => f.name.endsWith('.ris') || f.name.endsWith('.txt'))
    if (risFiles.length === 0) return
    const allRefs = []
    for (const file of risFiles) {
      const text = await file.text()
      allRefs.push(...parseRIS(text))
    }
    if (allRefs.length > 0) {
      await refsStore.addReferences(allRefs)
      toastStore.showToast(`成功导入 ${allRefs.length} 条文献`)
    } else {
      toastStore.showToast('未找到可导入的文献数据', 'error')
    }
  }
  input.click()
}

function onImportJSON() {
  showImportModal.value = false
  showAddMenu.value = false
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      if (!data.export_version) {
        toastStore.showToast('无效的备份文件格式', 'error')
        return
      }
      const res = await fetch('/api/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...auth.getHeaders() },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '导入失败')
      }
      await Promise.all([refsStore.loadReferences(), groupsStore.loadGroups(), notesStore.loadNotes(), refsStore.loadTrash()])
      toastStore.showToast('导入成功')
    } catch (e) {
      toastStore.showToast('导入失败: ' + e.message, 'error')
    }
  }
  input.click()
}
</script>

<template>
  <div class="ref-list-panel">
    <div class="list-header">
      <span class="list-title">{{ refsStore.isTrashMode ? '回收站' : '文献列表' }}</span>
      <div class="list-header-right" v-if="!refsStore.isTrashMode">
        <!-- sort direction toggle -->
        <button class="btn-sort" @click="refsStore.toggleSort" :title="refsStore.sortOrder === 'desc' ? '降序' : '升序'">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <polyline v-if="refsStore.sortOrder === 'desc'" points="19 12 12 19 5 12"/>
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
              <button class="sort-dropdown-item" :class="{ active: refsStore.sortField === 'year' }" @click="onPickField('year')">文献年份</button>
              <button class="sort-dropdown-item" :class="{ active: refsStore.sortField === 'created' }" @click="onPickField('created')">添加时间</button>
              <button class="sort-dropdown-item" :class="{ active: refsStore.sortField === 'note' }" @click="onPickField('note')">笔记更新时间</button>
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
        <!-- 新建/导入 下拉 -->
        <div class="add-menu-wrapper" ref="addMenuRef">
          <button class="btn-sort btn-add" :class="{ active: showAddMenu }" @click="toggleAddMenu" title="新建 / 导入">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>
          <Transition name="dropdown">
            <div v-if="showAddMenu" class="add-dropdown">
              <button class="add-dropdown-item" @click="onNewRef">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                <span>新建文献</span>
              </button>
              <div class="add-dropdown-divider"></div>
              <button class="add-dropdown-item" @click="showImportModal = true; showAddMenu = false">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span>导入文献</span>
              </button>
            </div>
          </Transition>
        </div>
        <span class="ref-count">{{ refsStore.filteredReferences.length }} 篇</span>
      </div>
      <div class="list-header-right" v-else>
        <button v-if="refsStore.trashReferences.length > 0" class="btn-sort btn-clear-trash" @click="clearTrashConfirm = true" title="清空回收站">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>
          </svg>
        </button>
        <span class="ref-count trash-hint">{{ refsStore.filteredReferences.length }} 篇 · 30天后自动清除</span>
      </div>
    </div>
    <div class="list-search">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" placeholder="搜索标题、摘要、作者、笔记..." v-model="refsStore.searchQuery">
      <button v-if="refsStore.searchQuery" class="btn-search-clear" @click="refsStore.searchQuery = ''" title="清空搜索">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <div class="ref-list" ref="listRef">
      <div v-if="refsStore.references.length === 0 && !refsStore.isTrashMode" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <p>拖拽 .ris 文件到此处<br>或点击上方 + 按钮导入文献</p>
      </div>
      <div v-else-if="refsStore.isTrashMode && refsStore.trashReferences && refsStore.trashReferences.length === 0" class="empty-state">
        <p>回收站为空</p>
      </div>
      <div v-else-if="refsStore.filteredReferences.length === 0" class="empty-state">
        <p>当前分组没有文献</p>
      </div>
      <template v-else>
        <div
          v-for="ref in refsStore.filteredReferences"
          :key="ref.id"
          class="ref-card"
          :class="{ active: refsStore.selectedReference?.id === ref.id }"
          @click="onClickRef(ref)"
        >
          <div class="ref-card-main">
            <div class="ref-card-title" v-html="highlightText(ref.title || '无标题', refsStore.searchQuery)"></div>
            <div class="ref-card-meta">
              <span class="ref-card-authors" v-html="highlightText(getAuthorDisplay(ref.authors), refsStore.searchQuery)"></span>
              <span v-if="ref.year" class="ref-card-year">{{ ref.year }}</span>
              <span v-if="ref.journal" class="ref-card-journal">{{ ref.journal }}</span>
            </div>
          </div>
          <span v-if="notesStore.hasNote(ref.id)" class="ref-card-note-badge" title="有笔记"></span>
        </div>
      </template>
    </div>

    <ConfirmDialog
      :visible="clearTrashConfirm"
      title="清空回收站"
      :message="`确定清空回收站中的全部 ${refsStore.trashReferences.length} 篇文献吗？此操作不可撤销。`"
      @confirm="onConfirmClearTrash"
      @cancel="clearTrashConfirm = false"
    />

    <!-- 导入格式选择弹框 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showImportModal" class="pwd-modal-overlay" @click.self="showImportModal = false">
          <div class="pwd-modal import-modal">
            <div class="pwd-modal-header">
              <span>选择导入格式</span>
              <button class="pwd-modal-close" @click="showImportModal = false">&times;</button>
            </div>
            <div class="import-modal-body">
              <button class="import-option" @click="onImportRIS">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
                <div class="import-option-text">
                  <span class="import-option-title">RIS 文件</span>
                  <span class="import-option-desc">导入 .ris 或 .txt 格式的文献数据</span>
                </div>
              </button>
              <button class="import-option" @click="onImportJSON">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15v-2h2a1 1 0 1 0 0-2H9"/>
                </svg>
                <div class="import-option-text">
                  <span class="import-option-title">JSON 备份文件</span>
                  <span class="import-option-desc">导入包含分组、文献和笔记的完整备份</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <ReferenceEditor v-if="showNewRefModal" @close="showNewRefModal = false" />
  </div>
</template>

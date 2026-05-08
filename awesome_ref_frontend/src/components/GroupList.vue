<script setup>
import { ref } from 'vue'
import { useGroups } from '../composables/useGroups.js'
import { useReferences } from '../composables/useReferences.js'
import { useToast } from '../composables/useToast.js'
import ConfirmDialog from './ConfirmDialog.vue'

const { groups, addGroup, deleteGroup, renameGroup } = useGroups()
const { activeGroupId, setActiveGroup, references, trashCount, loadTrash } = useReferences()
const { showToast } = useToast()

const showForm = ref(false)
const newName = ref('')
const editingId = ref(null)
const editName = ref('')
const confirmState = ref({ visible: false, groupId: null })


function onCreate() {
  if (!newName.value.trim()) return
  addGroup(newName.value)
  newName.value = ''
  showForm.value = false
  showToast('分组创建成功')
}

function onDelete(e, id) {
  e.stopPropagation()
  confirmState.value = { visible: true, groupId: id }
}

async function onConfirmDelete() {
  const id = confirmState.value.groupId
  confirmState.value = { visible: false, groupId: null }
  if (id) {
    const ok = await deleteGroup(id)
    if (ok) {
      showToast('分组已删除')
      if (activeGroupId.value === id) {
        setActiveGroup('all')
      }
    }
  }
}

function onCancelDelete() {
  confirmState.value = { visible: false, groupId: null }
}

function onStartRename(e, group) {
  e.stopPropagation()
  editingId.value = group.id
  editName.value = group.name
}

function onConfirmRename(e) {
  e.stopPropagation()
  if (editName.value.trim() && editingId.value) {
    renameGroup(editingId.value, editName.value)
  }
  editingId.value = null
  editName.value = ''
}

function onCancelRename(e) {
  e.stopPropagation()
  editingId.value = null
  editName.value = ''
}

function getCount(groupId) {
  if (groupId === 'all') return references.value.length
  if (groupId === 'trash') return trashCount.value
  return references.value.filter(r => (r.groupIds || []).includes(groupId)).length
}

async function onOpenTrash() {
  await loadTrash()
  setActiveGroup('trash')
}
</script>

<template>
  <div class="group-panel">
    <div class="group-header">
      <span class="group-title">分组</span>
      <button class="btn-add-group" @click="showForm = !showForm" title="新建分组">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
      </button>
    </div>

    <div v-if="showForm" class="group-form">
      <input
        v-model="newName"
        class="group-input"
        placeholder="分组名称"
        @keyup.enter="onCreate"
        @keyup.escape="showForm = false"
        autofocus
      >
      <div class="group-form-actions">
        <button class="btn-sm btn-cancel" @click="showForm = false">取消</button>
        <button class="btn-sm btn-confirm" @click="onCreate">创建</button>
      </div>
    </div>

    <!-- 全部 -->
    <div
      class="group-item"
      :class="{ active: activeGroupId === 'all' }"
      @click="setActiveGroup('all')"
    >
      <span class="group-item-icon">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
      </span>
      <span class="group-item-name">全部文献</span>
      <span class="group-item-count">{{ getCount('all') }}</span>
    </div>

    <!-- 回收站 -->
    <div
      class="group-item"
      :class="{ active: activeGroupId === 'trash' }"
      @click="onOpenTrash"
    >
      <span class="group-item-icon">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
      </span>
      <span class="group-item-name">回收站</span>
      <span class="group-item-count">{{ getCount('trash') }}</span>
    </div>

    <!-- 分组列表 -->
    <div
      v-for="group in groups"
      :key="group.id"
      class="group-item"
      :class="{ active: activeGroupId === group.id }"
      @click="setActiveGroup(group.id)"
    >
      <span class="group-item-icon">
        <svg v-if="group.id === 'ungrouped'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 7V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v3"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
      </span>

      <template v-if="editingId === group.id">
        <input
          v-model="editName"
          class="group-rename-input"
          @keyup.enter="onConfirmRename"
          @keyup.escape="onCancelRename"
          @blur="onConfirmRename"
          @click.stop
          autofocus
        >
      </template>
      <template v-else>
        <span class="group-item-name">{{ group.name }}</span>
        <span class="group-item-count">{{ getCount(group.id) }}</span>
        <div class="group-item-actions" v-if="group.id !== 'ungrouped'">
          <button class="btn-group-action" @click.stop="onStartRename($event, group)" title="重命名">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
            </svg>
          </button>
          <button class="btn-group-action btn-group-delete" @click="onDelete($event, group.id)" title="删除">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </template>
    </div>
  </div>

  <ConfirmDialog
    :visible="confirmState.visible"
    title="删除分组"
    message="确定删除该分组吗？分组内的文献将移除该分组标签。"
    @confirm="onConfirmDelete"
    @cancel="onCancelDelete"
  />
</template>

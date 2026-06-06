<script setup>
import { ref, watch, nextTick } from 'vue'
import { useGroupsStore } from '../stores/groups.js'
import { useReferencesStore } from '../stores/references.js'
import { useToastStore } from '../stores/toast.js'
import ConfirmDialog from './ConfirmDialog.vue'

const groupsStore = useGroupsStore()
const refsStore = useReferencesStore()
const toastStore = useToastStore()

const showForm = ref(false)
const newName = ref('')
const editingId = ref(null)
const editName = ref('')
const newGroupInputRef = ref(null)

watch(showForm, (v) => {
  if (v) nextTick(() => newGroupInputRef.value?.focus())
})
const confirmState = ref({ visible: false, groupId: null })

function onCreate() {
  if (!newName.value.trim()) return
  groupsStore.addGroup(newName.value)
  newName.value = ''
  showForm.value = false
  toastStore.showToast('分组创建成功')
}

function onDelete(e, id) {
  e.stopPropagation()
  confirmState.value = { visible: true, groupId: id }
}

async function onConfirmDelete() {
  const id = confirmState.value.groupId
  confirmState.value = { visible: false, groupId: null }
  if (id) {
    const ok = await groupsStore.deleteGroup(id)
    if (ok) {
      toastStore.showToast('分组已删除')
      if (refsStore.activeGroupId === id) {
        refsStore.setActiveGroup('all')
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
  nextTick(() => {
    const el = document.querySelector('.group-rename-input')
    if (el) { el.focus(); el.select() }
  })
}

function onConfirmRename(e) {
  if (e) e.stopPropagation()
  const trimmed = editName.value.trim()
  if (trimmed && editingId.value) {
    const group = groupsStore.groups.find(g => g.id === editingId.value)
    if (group && group.name !== trimmed) {
      groupsStore.renameGroup(editingId.value, editName.value)
    }
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
  if (groupId === 'all') return refsStore.references.length
  if (groupId === 'trash') return refsStore.trashCount
  return refsStore.references.filter(r => (r.groupIds || []).includes(groupId)).length
}

async function onOpenTrash() {
  await refsStore.loadTrash()
  refsStore.setActiveGroup('trash')
}

function onClickRecent(refId) {
  refsStore.setActiveGroup('all')
  refsStore.selectById(refId)
}
</script>

<template>
  <div class="group-panel">
    <div class="group-header">
      <span class="group-title">分组</span>
      <div class="group-header-actions">
        <button class="btn-add-group" @click="showForm = !showForm" title="新建分组">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="showForm" class="group-form">
      <input
        v-model="newName"
        ref="newGroupInputRef"
        class="group-input"
        placeholder="分组名称"
        @keyup.enter="onCreate"
        @keyup.escape="showForm = false"
      >
      <div class="group-form-actions">
        <button class="btn-sm btn-cancel" @click="showForm = false">取消</button>
        <button class="btn-sm btn-confirm" @click="onCreate">创建</button>
      </div>
    </div>

    <!-- 全部 -->
    <div
      class="group-item"
      :class="{ active: refsStore.activeGroupId === 'all' }"
      @click="refsStore.setActiveGroup('all')"
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
      :class="{ active: refsStore.activeGroupId === 'trash' }"
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
      v-for="group in groupsStore.groups"
      :key="group.id"
      class="group-item"
      :class="{ active: refsStore.activeGroupId === group.id }"
      @click="refsStore.setActiveGroup(group.id)"
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
        >
      </template>
      <template v-else>
        <span class="group-item-name">{{ group.name }}</span>
        <span class="group-item-count">{{ getCount(group.id) }}</span>
        <div class="group-item-actions" v-if="group.id !== 'ungrouped'">
          <button class="btn-group-action" @mousedown.prevent.stop @click="onStartRename($event, group)" title="重命名">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
            </svg>
          </button>
          <button class="btn-group-action btn-group-delete" @mousedown.prevent.stop @click="onDelete($event, group.id)" title="删除">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </template>
    </div>
  </div>

  <div v-if="refsStore.recentRefs.length" class="recent-refs">
    <div class="recent-refs-header">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
      </svg>
      <span>最近浏览</span>
    </div>
    <div
      v-for="r in refsStore.recentRefs"
      :key="r.id"
      class="recent-ref-item"
      @click="onClickRecent(r.id)"
      :title="r.title"
    >
      {{ r.title }}
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

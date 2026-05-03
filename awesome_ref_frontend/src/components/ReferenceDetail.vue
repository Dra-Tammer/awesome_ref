<script setup>
import { ref, computed } from 'vue'
import { useReferences } from '../composables/useReferences.js'
import { useGroups } from '../composables/useGroups.js'
import { useToast } from '../composables/useToast.js'
import { getRISTypeLabel } from '../utils/risParser.js'
import { highlightText } from '../utils/highlight.js'
import NoteEditor from './NoteEditor.vue'
import ConfirmDialog from './ConfirmDialog.vue'

const { selectedReference, addRefToGroup, removeRefFromGroup, searchQuery, isTrashMode, softDeleteRef, restoreRef, permanentDeleteRef } = useReferences()
const { groups } = useGroups()
const { showToast } = useToast()

const sortedGroups = computed(() => {
  const arr = groups.value || []
  return [...arr].sort((a, b) => {
    if (a.id === 'ungrouped') return -1
    if (b.id === 'ungrouped') return 1
    return 0
  })
})

const deleteConfirm = ref({ visible: false, permanent: false })

function getDoiLink(doi) {
  if (!doi) return '#'
  return doi.startsWith('http') ? doi : `https://doi.org/${doi}`
}

function getVolumeIssue(vol, issue) {
  let str = ''
  if (vol) str = 'Vol. ' + vol
  if (issue) str += (str ? ', ' : '') + 'No. ' + issue
  return str || '—'
}

function isInGroup(groupKey) {
  return selectedReference.value?.groupIds?.includes(groupKey) || false
}

function toggleGroup(groupKey) {
  if (!selectedReference.value) return
  if (isInGroup(groupKey)) {
    removeRefFromGroup(selectedReference.value.id, groupKey)
  } else {
    addRefToGroup(selectedReference.value.id, groupKey)
  }
}

function onDeleteClick() {
  deleteConfirm.value = { visible: true, permanent: false }
}

function onPermanentDeleteClick() {
  deleteConfirm.value = { visible: true, permanent: true }
}

async function onConfirmDelete() {
  const { permanent } = deleteConfirm.value
  const refKey = selectedReference.value?.id
  deleteConfirm.value = { visible: false, permanent: false }
  if (!refKey) return
  if (permanent) {
    const ok = await permanentDeleteRef(refKey)
    if (ok) showToast('文献已永久删除，无法撤回', 'error')
  } else {
    const ok = await softDeleteRef(refKey)
    if (ok) showToast('删除成功，可在回收站撤回')
  }
}

function onCancelDelete() {
  deleteConfirm.value = { visible: false, permanent: false }
}

async function onRestore() {
  const ok = await restoreRef(selectedReference.value?.id)
  if (ok) showToast('文献已恢复')
}
</script>

<template>
  <main class="detail-panel">
    <!-- 空状态 -->
    <div v-if="!selectedReference" class="detail-empty">
      <div class="empty-illustration">
        <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.8" opacity="0.25">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          <line x1="8" y1="7" x2="16" y2="7" opacity="0.5"/>
          <line x1="8" y1="10" x2="14" y2="10" opacity="0.5"/>
          <line x1="8" y1="13" x2="16" y2="13" opacity="0.5"/>
        </svg>
      </div>
      <h2>选择一篇文献查看详情</h2>
      <p>从左侧列表中选择文献，或导入新的 RIS 文件</p>
    </div>

    <!-- 详情内容 -->
    <div v-else class="detail-content">
      <!-- 1. 标题 -->
      <div class="detail-header">
        <div class="detail-header-top">
          <div class="detail-header-row">
            <span class="detail-type" :title="selectedReference.journal || getRISTypeLabel(selectedReference.type)">{{ selectedReference.journal || getRISTypeLabel(selectedReference.type) }}</span>
            <!-- 正常模式：删除按钮 -->
            <template v-if="!isTrashMode">
              <button class="btn-detail-delete" @click="onDeleteClick" title="移入回收站">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </template>
            <!-- 回收站模式：恢复+永久删除 -->
            <template v-else>
              <div class="trash-detail-actions">
                <button class="btn-restore" @click="onRestore">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                  </svg>
                  恢复文献
                </button>
                <button class="btn-permanent-delete" @click="onPermanentDeleteClick">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                  永久删除
                </button>
              </div>
            </template>
          </div>
          <!-- 分组标签在下方 -->
          <div class="group-chips" v-if="!isTrashMode">
            <span
              v-for="g in sortedGroups"
              :key="g.id"
              class="group-chip"
              :class="{ active: isInGroup(g.id), 'group-chip-disabled': g.id === 'ungrouped' }"
              @click="g.id !== 'ungrouped' && toggleGroup(g.id)"
            >{{ g.name }}</span>
          </div>
        </div>
        <h2 class="detail-title" v-html="highlightText(selectedReference.title || '无标题', searchQuery)"></h2>
      </div>

      <!-- 2. 笔记 -->
      <NoteEditor v-if="!isTrashMode" :ref-id="selectedReference.id" />

      <!-- 3. 摘要 -->
      <div v-if="selectedReference.abstract" class="detail-section">
        <label>摘要</label>
        <p class="detail-abstract" v-html="highlightText(selectedReference.abstract, searchQuery)"></p>
      </div>

      <!-- 4. 元数据 -->
      <div class="detail-section">
        <div class="detail-field">
          <label>作者</label>
          <div class="detail-authors">
            <span v-if="selectedReference.authors.length === 0" style="color:#9ca3af">未知作者</span>
            <span v-for="(a, i) in selectedReference.authors" :key="i" class="author-chip" v-html="highlightText(a, searchQuery)"></span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-field">
            <label>年份</label>
            <span>{{ selectedReference.year || '—' }}</span>
          </div>
          <div class="detail-field">
            <label>期刊</label>
            <span>{{ selectedReference.journal || '—' }}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-field">
            <label>卷 / 期</label>
            <span>{{ getVolumeIssue(selectedReference.volume, selectedReference.issue) }}</span>
          </div>
          <div class="detail-field">
            <label>页码</label>
            <span>{{ selectedReference.pages || '—' }}</span>
          </div>
        </div>
        <div class="detail-field">
          <label>DOI</label>
          <a
            v-if="selectedReference.doi"
            class="detail-doi"
            :href="getDoiLink(selectedReference.doi)"
            target="_blank"
            rel="noopener"
          >{{ selectedReference.doi }}</a>
          <span v-else>—</span>
        </div>
      </div>

      <!-- 5. 关键词 -->
      <div v-if="selectedReference.keywords.length > 0" class="detail-section">
        <label>关键词</label>
        <div class="detail-keywords">
          <span v-for="(k, i) in selectedReference.keywords" :key="i" class="keyword-tag">{{ k }}</span>
        </div>
      </div>
    </div>

    <ConfirmDialog
      :visible="deleteConfirm.visible"
      :title="deleteConfirm.permanent ? '永久删除' : '移入回收站'"
      :message="deleteConfirm.permanent
        ? `确定永久删除《${selectedReference?.title || ''}》吗？此操作不可撤销。`
        : `确定将《${selectedReference?.title || ''}》移入回收站吗？`"
      @confirm="onConfirmDelete"
      @cancel="onCancelDelete"
    />
  </main>
</template>

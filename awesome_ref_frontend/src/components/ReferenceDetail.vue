<script setup>
import { ref, computed } from 'vue'
import { useReferences } from '../composables/useReferences.js'
import { useGroups } from '../composables/useGroups.js'
import { useToast } from '../composables/useToast.js'
import { getRISTypeLabel } from '../utils/risParser.js'
import { highlightText } from '../utils/highlight.js'
import NoteEditor from './NoteEditor.vue'
import ConfirmDialog from './ConfirmDialog.vue'

const { selectedReference, addRefToGroup, removeRefFromGroup, searchQuery, isTrashMode, softDeleteRef, restoreRef, permanentDeleteRef, uploadPdf, deletePdf } = useReferences()
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

function onPdfClick() {
  if (!selectedReference.value) return
  if (selectedReference.value.pdfFilename) {
    window.open(`/api/references/${encodeURIComponent(selectedReference.value.id)}/pdf`, '_blank')
  } else {
    triggerPdfUpload()
  }
}

function onPdfDownload() {
  if (!selectedReference.value) return
  window.open(`/api/references/${encodeURIComponent(selectedReference.value.id)}/pdf?download=1`, '_blank')
}

function triggerPdfUpload() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.pdf'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      await uploadPdf(selectedReference.value.id, file)
      showToast('PDF 上传成功')
    } catch (e) {
      showToast('PDF 上传失败: ' + e.message, 'error')
    }
  }
  input.click()
}

function onPdfReplace() {
  triggerPdfUpload()
}

async function onPdfDelete() {
  const ok = await deletePdf(selectedReference.value.id)
  if (ok) showToast('PDF 已移除')
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
      <p>从列表中选择文献，或导入新的 RIS 文件</p>
    </div>

    <!-- 详情内容 -->
    <div v-else class="detail-content">
      <!-- 1. 标题 -->
      <div class="detail-header">
        <div class="detail-header-top">
          <div class="detail-header-row">
            <span class="detail-type" :title="selectedReference.journal || getRISTypeLabel(selectedReference.type)">{{ selectedReference.journal || getRISTypeLabel(selectedReference.type) }}</span>
            <!-- 正常模式：PDF链接 + 删除按钮 -->
            <template v-if="!isTrashMode">
              <div class="detail-actions">
                <div class="detail-pdf-group">
                  <button
                    class="btn-detail-pdf"
                    :class="{ linked: selectedReference.pdfFilename }"
                    @click="onPdfClick"
                    :title="selectedReference.pdfFilename ? '打开 PDF' : '上传 PDF'"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                    </svg>
                  </button>
                  <div v-if="selectedReference.pdfFilename" class="pdf-actions-dropdown">
                    <button class="pdf-action-item" @click="onPdfDownload" title="下载 PDF">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                      </svg>
                    </button>
                    <button class="pdf-action-item" @click="onPdfReplace" title="替换 PDF">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                      </svg>
                    </button>
                    <button class="pdf-action-item danger" @click="onPdfDelete" title="移除 PDF">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <button class="btn-detail-delete" @click="onDeleteClick" title="移入回收站">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
              </div>
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

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useReferencesStore } from '../stores/references.js'
import { useNotesStore } from '../stores/notes.js'
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import { useToastStore } from '../stores/toast.js'
import { useResizablePanels } from '../composables/useResizablePanels.js'
import GroupList from '../components/GroupList.vue'
import ReferenceList from '../components/ReferenceList.vue'
import ReferenceDetail from '../components/ReferenceDetail.vue'
import DropOverlay from '../components/DropOverlay.vue'
import { parseRIS } from '../utils/risParser.js'

const refsStore = useReferencesStore()
const notesStore = useNotesStore()
const toastStore = useToastStore()

const {
  leftWidth, leftCollapsed, resizingLeft, onLeftHandleDown, toggleLeftPanel,
  rightWidth, rightCollapsed, resizingRight, onRightHandleDown, toggleRightPanel,
} = useResizablePanels({ leftDefault: 240, rightDefault: 780, rightMin: 320 })

// Auto-expand right panel when a reference is selected
watch(() => refsStore.selectedReference, (ref) => {
  if (ref && rightCollapsed.value) {
    toggleRightPanel()
  }
})

// Sync notes to references store
watch(() => notesStore.notes, (val) => refsStore.setNotes(val), { immediate: true })

async function handleDropFiles(files) {
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
</script>

<template>
  <div class="main">
    <aside
      class="side-panel left-panel"
      :class="{ collapsed: leftCollapsed, resizing: resizingLeft }"
      :style="{ width: leftWidth + 'px' }"
    >
      <div class="panel-content" :class="{ hidden: leftCollapsed }">
        <GroupList />
      </div>
    </aside>
    <div
      class="resize-handle"
      :class="{ active: resizingLeft, collapsed: leftCollapsed }"
      @mousedown="onLeftHandleDown"
    >
      <span class="collapse-arrow" :class="{ visible: leftCollapsed }" title="展开分组面板">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </span>
    </div>
    <section class="middle-panel">
      <ReferenceList />
    </section>
    <div
      class="resize-handle"
      :class="{ active: resizingRight, collapsed: rightCollapsed }"
      @mousedown="onRightHandleDown"
    >
      <span class="collapse-arrow" :class="{ visible: rightCollapsed }" title="展开详情面板">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </span>
    </div>
    <aside
      class="side-panel right-panel"
      :class="{ collapsed: rightCollapsed, resizing: resizingRight }"
      :style="{ width: rightWidth + 'px' }"
    >
      <div class="panel-content" :class="{ hidden: rightCollapsed }">
        <ReferenceDetail />
      </div>
    </aside>
    <DropOverlay :on-files="handleDropFiles" />
  </div>
</template>

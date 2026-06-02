<script setup>
import { ref, watch, onMounted } from 'vue'
import { useReferencesStore } from '../stores/references.js'
import { useNotesStore } from '../stores/notes.js'
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import GroupList from '../components/GroupList.vue'
import ReferenceList from '../components/ReferenceList.vue'
import ReferenceDetail from '../components/ReferenceDetail.vue'
import DropOverlay from '../components/DropOverlay.vue'
import { parseRIS } from '../utils/risParser.js'

const refsStore = useReferencesStore()
const notesStore = useNotesStore()

// Left sidebar (GroupList)
const leftWidth = ref(240)
const leftCollapsed = ref(false)
const leftPrevWidth = ref(240)

// Right sidebar (ReferenceDetail)
const rightWidth = ref(780)
const rightCollapsed = ref(false)
const rightPrevWidth = ref(780)

const resizingLeft = ref(false)
const resizingRight = ref(false)
let leftRaf = null
let rightRaf = null

function onLeftHandleDown(e) {
  e.preventDefault()
  if (leftCollapsed.value) {
    toggleLeftPanel()
    return
  }
  const startX = e.clientX
  const startW = leftWidth.value
  let moved = false

  function onMove(ev) {
    if (!moved && Math.abs(ev.clientX - startX) > 3) moved = true
    if (!moved) return
    resizingLeft.value = true
    if (leftRaf) cancelAnimationFrame(leftRaf)
    leftRaf = requestAnimationFrame(() => {
      leftWidth.value = Math.max(180, Math.min(400, startW + ev.clientX - startX))
    })
  }

  function onUp() {
    resizingLeft.value = false
    if (leftRaf) cancelAnimationFrame(leftRaf)
    leftRaf = null
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    if (!moved) toggleLeftPanel()
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function onRightHandleDown(e) {
  e.preventDefault()
  if (rightCollapsed.value) {
    toggleRightPanel()
    return
  }
  const startX = e.clientX
  const startW = rightWidth.value
  let moved = false

  function onMove(ev) {
    if (!moved && Math.abs(ev.clientX - startX) > 3) moved = true
    if (!moved) return
    resizingRight.value = true
    if (rightRaf) cancelAnimationFrame(rightRaf)
    rightRaf = requestAnimationFrame(() => {
      rightWidth.value = Math.max(320, Math.min(800, startW + startX - ev.clientX))
    })
  }

  function onUp() {
    resizingRight.value = false
    if (rightRaf) cancelAnimationFrame(rightRaf)
    rightRaf = null
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    if (!moved) toggleRightPanel()
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function toggleLeftPanel() {
  if (leftCollapsed.value) {
    leftCollapsed.value = false
    leftWidth.value = leftPrevWidth.value
  } else {
    leftPrevWidth.value = leftWidth.value
    leftCollapsed.value = true
    leftWidth.value = 0
  }
}

function toggleRightPanel() {
  if (rightCollapsed.value) {
    rightCollapsed.value = false
    rightWidth.value = rightPrevWidth.value
  } else {
    rightPrevWidth.value = rightWidth.value
    rightCollapsed.value = true
    rightWidth.value = 0
  }
}

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
  if (allRefs.length > 0) await refsStore.addReferences(allRefs)
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

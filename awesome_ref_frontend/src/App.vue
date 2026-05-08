<script setup>
import { onMounted, ref, watch } from 'vue'
import { useAuth } from './composables/useAuth.js'
import { useReferences } from './composables/useReferences.js'
import { useNotes } from './composables/useNotes.js'
import { useGroups } from './composables/useGroups.js'
import { parseRIS } from './utils/risParser.js'
import LoginPage from './components/LoginPage.vue'
import Toolbar from './components/Toolbar.vue'
import GroupList from './components/GroupList.vue'
import ReferenceList from './components/ReferenceList.vue'
import ReferenceDetail from './components/ReferenceDetail.vue'
import DropOverlay from './components/DropOverlay.vue'

const checking = ref(true)
const { isLoggedIn, tryRestoreSession } = useAuth()
const { loadReferences, loadTrash, addReferences, setNotes, resetAll, selectedReference, selectedIndex, filteredReferences, selectByIndex } = useReferences()
const { loadNotes, notes, resetNotes } = useNotes()
const { loadGroups, resetGroups } = useGroups()

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
watch(selectedReference, (ref) => {
  if (ref && rightCollapsed.value) {
    toggleRightPanel()
  }
})

watch(notes, (val) => setNotes(val), { immediate: true })

watch(isLoggedIn, async (loggedIn) => {
  if (loggedIn) {
    await Promise.all([loadReferences(), loadNotes(), loadGroups(), loadTrash()])
  } else {
    resetAll()
    resetNotes()
    resetGroups()
  }
})

onMounted(async () => {
  const restored = await tryRestoreSession()
  if (restored) {
    await Promise.all([loadReferences(), loadNotes(), loadGroups(), loadTrash()])
  }
  checking.value = false

  // Global keyboard navigation for reference list
  window.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
    const list = filteredReferences.value
    if (!list || list.length === 0) return
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (selectedIndex.value > 0) selectByIndex(selectedIndex.value - 1)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (selectedIndex.value < list.length - 1) selectByIndex(selectedIndex.value + 1)
    }
  })
})

async function handleDropFiles(files) {
  const risFiles = files.filter(f => f.name.endsWith('.ris') || f.name.endsWith('.txt'))
  if (risFiles.length === 0) return
  const allRefs = []
  for (const file of risFiles) {
    const text = await file.text()
    allRefs.push(...parseRIS(text))
  }
  if (allRefs.length > 0) await addReferences(allRefs)
}
</script>

<template>
  <Transition name="page" mode="out-in">
    <div v-if="checking" key="loading" class="app-loading">
      <div class="loading-spinner">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        <p>加载中...</p>
      </div>
    </div>
    <LoginPage v-else-if="!isLoggedIn" key="login" />

    <div v-else class="app" key="main">
      <Toolbar />
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
      </div>
      <DropOverlay :on-files="handleDropFiles" />
    </div>
  </Transition>
</template>

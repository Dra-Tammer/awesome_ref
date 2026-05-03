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
const { loadReferences, loadTrash, addReferences, setNotes, resetAll } = useReferences()
const { loadNotes, notes, resetNotes } = useNotes()
const { loadGroups, resetGroups } = useGroups()

// 侧边栏
const sidebarWidth = ref(360)
const collapsed = ref(false)
const prevWidth = ref(360)
const resizing = ref(false)
let rafId = null

function onDragStart(e) {
  e.preventDefault()
  resizing.value = true
  const startX = e.clientX
  const startW = sidebarWidth.value

  function onMove(ev) {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
      const delta = ev.clientX - startX
      sidebarWidth.value = Math.max(240, Math.min(600, startW + delta))
    })
  }

  function onUp() {
    resizing.value = false
    if (rafId) cancelAnimationFrame(rafId)
    rafId = null
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function toggleCollapse() {
  if (collapsed.value) {
    collapsed.value = false
    sidebarWidth.value = prevWidth.value
  } else {
    prevWidth.value = sidebarWidth.value
    collapsed.value = true
    sidebarWidth.value = 0
  }
}

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
    <div v-if="checking" key="loading" class="app-loading" />
    <LoginPage v-else-if="!isLoggedIn" key="login" />

    <div v-else class="app" key="main">
      <Toolbar :collapsed="collapsed" @toggle-sidebar="toggleCollapse" />
      <div class="main">
        <aside
          class="ref-list-panel"
          :class="{ collapsed, resizing }"
          :style="{ width: sidebarWidth + 'px' }"
        >
          <div class="sidebar-content" :class="{ hidden: collapsed }">
            <GroupList />
            <ReferenceList />
          </div>
        </aside>
        <div
          class="resize-handle"
          :class="{ active: resizing }"
          @mousedown="onDragStart"
        ></div>
        <ReferenceDetail />
      </div>
      <DropOverlay :on-files="handleDropFiles" />
    </div>
  </Transition>
</template>

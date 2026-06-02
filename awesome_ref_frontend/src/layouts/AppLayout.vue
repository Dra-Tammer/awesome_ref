<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useReferencesStore } from '../stores/references.js'
import { useNotesStore } from '../stores/notes.js'
import { useGroupsStore } from '../stores/groups.js'
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import { useDailyTasksStore } from '../stores/dailyTasks.js'
import Toolbar from '../components/Toolbar.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const refsStore = useReferencesStore()
const notesStore = useNotesStore()
const groupsStore = useGroupsStore()
const standaloneNotesStore = useStandaloneNotesStore()
const dailyTasksStore = useDailyTasksStore()

const checking = ref(true)

async function loadAllData() {
  await Promise.all([
    refsStore.loadReferences(),
    notesStore.loadNotes(),
    groupsStore.loadGroups(),
    refsStore.loadTrash(),
    standaloneNotesStore.loadNotes(),
    dailyTasksStore.loadToday(),
    dailyTasksStore.loadHeatmap(),
  ])
}

function resetAllData() {
  refsStore.resetAll()
  notesStore.resetNotes()
  groupsStore.resetGroups()
  standaloneNotesStore.resetNotes()
  dailyTasksStore.resetDailyTasks()
}

watch(() => auth.isLoggedIn, async (loggedIn) => {
  if (loggedIn) {
    await loadAllData()
  } else {
    resetAllData()
    router.push({ name: 'login' })
  }
})

onMounted(async () => {
  if (auth.isLoggedIn) {
    await loadAllData()
  }
  checking.value = false

  window.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
    const list = refsStore.filteredReferences
    if (!list || list.length === 0) return
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (refsStore.selectedIndex > 0) refsStore.selectByIndex(refsStore.selectedIndex - 1)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (refsStore.selectedIndex < list.length - 1) refsStore.selectByIndex(refsStore.selectedIndex + 1)
    }
  })
})

function handleGlobalNavigate(item) {
  if (item.type === 'ref') {
    router.push({ name: 'references' })
    refsStore.setActiveGroup('all')
    setTimeout(() => refsStore.selectById(item.id), 0)
  } else if (item.type === 'note') {
    router.push({ name: 'notes' })
    setTimeout(() => standaloneNotesStore.selectNote(item.raw), 0)
  } else if (item.type === 'group') {
    router.push({ name: 'references' })
    refsStore.setActiveGroup(item.id)
  }
}
</script>

<template>
  <div v-if="checking" class="app-loading">
    <div class="loading-spinner">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2">
        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
      </svg>
      <p>加载中...</p>
    </div>
  </div>

  <div v-else class="app">
    <Toolbar @navigate="handleGlobalNavigate" />
    <router-view v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
  </div>
</template>

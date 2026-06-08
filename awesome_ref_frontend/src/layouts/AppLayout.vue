<script setup>
import { watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useReferencesStore } from '../stores/references.js'
import { useNotesStore } from '../stores/notes.js'
import { useGroupsStore } from '../stores/groups.js'
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import { useDailyTasksStore } from '../stores/dailyTasks.js'
import { useStatsStore } from '../stores/stats.js'
import Toolbar from '../components/Toolbar.vue'

const router = useRouter()
const auth = useAuthStore()
const refsStore = useReferencesStore()
const notesStore = useNotesStore()
const groupsStore = useGroupsStore()
const standaloneNotesStore = useStandaloneNotesStore()
const dailyTasksStore = useDailyTasksStore()
const statsStore = useStatsStore()

async function loadAllData() {
  await Promise.all([
    refsStore.loadReferences(),
    notesStore.loadNotes(),
    groupsStore.loadGroups(),
    refsStore.loadTrash(),
    standaloneNotesStore.loadNotes(),
    standaloneNotesStore.loadTags(),
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
  statsStore.resetStats()
}

watch(() => auth.logged, async (loggedIn) => {
  if (loggedIn) {
    await loadAllData()
  } else {
    resetAllData()
    router.push({ name: 'login' })
  }
})

function handleKeydown(e) {
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
}

onMounted(async () => {
  if (auth.logged) {
    await loadAllData()
  }
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
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
  } else if (item.type === 'task') {
    router.push({ name: 'daily-tasks' })
    setTimeout(() => {
      dailyTasksStore.loadPlanByDate(item.raw.date)
    }, 0)
  }
}
</script>

<template>
  <div class="app">
    <Toolbar @navigate="handleGlobalNavigate" />
    <router-view v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
  </div>
</template>

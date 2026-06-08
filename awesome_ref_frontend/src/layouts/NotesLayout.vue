<script setup>
import { ref, watch } from 'vue'
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import { useResizablePanels } from '../composables/useResizablePanels.js'
import NoteList from '../components/NoteList.vue'
import StandaloneNoteEditor from '../components/StandaloneNoteEditor.vue'
import NoteOutline from '../components/NoteOutline.vue'

const standaloneNotesStore = useStandaloneNotesStore()

const {
  leftWidth, leftCollapsed, resizingLeft, onLeftHandleDown, toggleLeftPanel,
  rightWidth, rightCollapsed, resizingRight, onRightHandleDown, toggleRightPanel,
} = useResizablePanels({ leftDefault: 280, rightDefault: 360, rightMin: 240 })

// Auto-select first note when entering notes view
watch(() => standaloneNotesStore.notes, (notes) => {
  if (!standaloneNotesStore.selectedNote && notes.length > 0) {
    standaloneNotesStore.selectNote(notes[0])
  }
}, { immediate: true })

// Auto-expand right panel when a note is selected
watch(() => standaloneNotesStore.selectedNote, (note) => {
  if (note && rightCollapsed.value) {
    toggleRightPanel()
  }
})
</script>

<template>
  <div class="main">
    <aside
      class="side-panel left-panel"
      :class="{ collapsed: leftCollapsed, resizing: resizingLeft }"
      :style="{ width: leftWidth + 'px' }"
    >
      <div class="panel-content" :class="{ hidden: leftCollapsed }">
        <NoteList />
      </div>
    </aside>
    <div
      class="resize-handle"
      :class="{ active: resizingLeft, collapsed: leftCollapsed }"
      @mousedown="onLeftHandleDown"
    >
      <span class="collapse-arrow" :class="{ visible: leftCollapsed }" title="展开笔记列表">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </span>
    </div>
    <section class="middle-panel">
      <StandaloneNoteEditor />
    </section>
    <div
      class="resize-handle"
      :class="{ active: resizingRight, collapsed: rightCollapsed }"
      @mousedown="onRightHandleDown"
    >
      <span class="collapse-arrow" :class="{ visible: rightCollapsed }" title="展开大纲">
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
        <NoteOutline />
      </div>
    </aside>
  </div>
</template>

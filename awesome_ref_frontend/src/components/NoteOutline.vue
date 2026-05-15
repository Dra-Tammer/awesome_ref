<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useStandaloneNotes } from '../composables/useStandaloneNotes.js'

const { selectedNote } = useStandaloneNotes()

const headings = ref([])
const activeId = ref(null)

function parseHeadings(md) {
  if (!md) return []
  const result = []
  const lines = md.split('\n')
  for (const line of lines) {
    const m = line.match(/^(#{1,6})\s+(.+)/)
    if (m) {
      const level = m[1].length
      const text = m[2].trim()
      // Skip h4-h6; only show h1-h3
      if (level > 3) continue
      const id = slugify(text)
      result.push({ level, text, id })
    }
  }
  return result
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w一-鿿\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
}

watch(() => selectedNote.value?.content, (content) => {
  headings.value = parseHeadings(content)
  activeId.value = null
}, { immediate: true })

const visibleHeadings = computed(() => {
  if (headings.value.length === 0) return []
  return headings.value
})

function scrollToHeading(heading) {
  // Try to find the heading element in the preview area
  const preview = document.querySelector('.note-editor-preview')
  if (!preview) return

  const headingElements = preview.querySelectorAll('h1, h2, h3, h4, h5, h6')
  let target = null
  for (const el of headingElements) {
    if (el.textContent?.trim() === heading.text) {
      target = el
      break
    }
  }

  if (target) {
    activeId.value = heading.id
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<template>
  <div class="outline-panel">
    <div class="outline-header">
      <span class="outline-title">大纲</span>
    </div>

    <div class="outline-body">
      <div v-if="!selectedNote" class="outline-empty">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.3">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        <p>选择笔记后显示大纲</p>
      </div>

      <div v-else-if="visibleHeadings.length === 0" class="outline-empty">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.3">
          <path d="M4 6h16M4 12h10M4 18h8"/>
        </svg>
        <p class="outline-empty-hint">使用标题语法<br>添加 H1~H3 标题</p>
      </div>

      <nav v-else class="outline-nav">
        <a
          v-for="(h, idx) in visibleHeadings"
          :key="idx"
          class="outline-item"
          :class="{
            [`outline-level-${h.level}`]: true,
            'outline-active': activeId === h.id,
          }"
          :title="h.text"
          @click.prevent="scrollToHeading(h)"
        >
          <span class="outline-bullet" :class="`bullet-h${h.level}`"></span>
          <span class="outline-text">{{ h.text }}</span>
        </a>
      </nav>
    </div>
  </div>
</template>

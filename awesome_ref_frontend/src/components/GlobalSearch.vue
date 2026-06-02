<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useReferencesStore } from '../stores/references.js'
import { useStandaloneNotesStore } from '../stores/standaloneNotes.js'
import { useGroupsStore } from '../stores/groups.js'
import { useNotesStore } from '../stores/notes.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'navigate'])

const refsStore = useReferencesStore()
const standaloneNotesStore = useStandaloneNotesStore()
const groupsStore = useGroupsStore()
const notesStore = useNotesStore()

const query = ref('')
const activeIndex = ref(0)
const inputRef = ref(null)
const resultRef = ref(null)

const MAX_PER_GROUP = 5

function onGlobalKeydown(e) {
  if (e.key === 'Escape' && props.visible) {
    e.preventDefault()
    emit('close')
  }
}
onMounted(() => window.addEventListener('keydown', onGlobalKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onGlobalKeydown))

watch(() => props.visible, (v) => {
  if (v) {
    query.value = ''
    activeIndex.value = 0
    nextTick(() => inputRef.value?.focus())
  }
})

watch(query, () => { activeIndex.value = 0 })

const groupedResults = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  const words = q.split(/\s+/)

  const match = (text) => {
    if (!text) return false
    const lower = text.toLowerCase()
    return words.every(w => lower.includes(w))
  }

  const refs = []
  for (const r of refsStore.references) {
    if (refs.length >= MAX_PER_GROUP) break
    const fields = [
      r.title, r.abstract, r.journal, r.doi,
      ...(r.authors || []), ...(r.keywords || []),
      notesStore.notes[r.id]?.content || '',
    ]
    if (fields.some(f => match(f))) {
      refs.push({
        id: r.id, type: 'ref',
        title: r.title || '无标题',
        sub: (r.authors || []).slice(0, 2).join(', ') + (r.year ? ` (${r.year})` : ''),
      })
    }
  }

  const notes = []
  for (const n of standaloneNotesStore.notes) {
    if (notes.length >= MAX_PER_GROUP) break
    if (match(n.title) || match(n.content)) {
      notes.push({
        id: n.id, type: 'note',
        title: n.title || '无标题笔记',
        sub: n.content ? n.content.replace(/[#*`~>\[\]()!|_\-]/g, '').trim().slice(0, 60) : '',
        raw: n,
      })
    }
  }

  const grps = []
  for (const g of groupsStore.groups) {
    if (grps.length >= MAX_PER_GROUP) break
    if (g.id === 'ungrouped') continue
    if (match(g.name)) {
      grps.push({
        id: g.id, type: 'group',
        title: g.name, sub: '',
      })
    }
  }

  const result = []
  if (refs.length) result.push({ label: '文献', items: refs })
  if (notes.length) result.push({ label: '笔记', items: notes })
  if (grps.length) result.push({ label: '分组', items: grps })
  return result
})

const flatItems = computed(() => {
  return groupedResults.value.flatMap(g => g.items)
})

function flatIndex(groupIdx, itemIdx) {
  let offset = 0
  for (let i = 0; i < groupIdx; i++) {
    offset += groupedResults.value[i].items.length
  }
  return offset + itemIdx
}

watch(activeIndex, () => {
  nextTick(() => {
    const el = resultRef.value?.querySelector('.search-panel-item.active')
    if (el) el.scrollIntoView({ block: 'nearest' })
  })
})

function onKeydown(e) {
  const total = flatItems.value.length

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (total) activeIndex.value = (activeIndex.value + 1) % total
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (total) activeIndex.value = (activeIndex.value - 1 + total) % total
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (total) goTo(flatItems.value[activeIndex.value])
  }
}

function goTo(item) {
  if (!item) return
  emit('navigate', item)
  emit('close')
}

function typeLabel(type) {
  return type === 'ref' ? '文献' : type === 'note' ? '笔记' : '分组'
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay search-overlay" @click.self="emit('close')">
        <div class="search-panel" @keydown="onKeydown">
          <!-- 搜索输入 -->
          <div class="search-panel-input-row">
            <svg class="search-panel-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              ref="inputRef"
              v-model="query"
              placeholder="搜索文献、笔记、分组..."
              spellcheck="false"
            />
            <span class="search-panel-esc">ESC</span>
          </div>

          <!-- 搜索结果 -->
          <div class="search-panel-results" ref="resultRef" v-if="groupedResults.length">
            <template v-for="(group, gi) in groupedResults" :key="gi">
              <div class="search-panel-group-label">{{ group.label }}</div>
              <div
                v-for="(item, ii) in group.items"
                :key="item.id"
                class="search-panel-item"
                :class="{ active: flatIndex(gi, ii) === activeIndex }"
                @click="goTo(item)"
                @mouseenter="activeIndex = flatIndex(gi, ii)"
              >
                <div class="search-panel-item-icon" :class="`type-${item.type}`">
                  <svg v-if="item.type === 'ref'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  </svg>
                  <svg v-else-if="item.type === 'note'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
                <div class="search-panel-item-text">
                  <span class="search-panel-item-title">{{ item.title }}</span>
                  <span class="search-panel-item-sub" v-if="item.sub">{{ item.sub }}</span>
                </div>
                <span class="search-panel-item-type">{{ typeLabel(item.type) }}</span>
              </div>
            </template>
          </div>

          <!-- 空状态 -->
          <div v-else-if="query.trim()" class="search-panel-empty">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="8" x2="14" y2="14"/><line x1="14" y1="8" x2="8" y2="14"/>
            </svg>
            <span>未找到匹配内容</span>
          </div>

          <!-- 初始提示 -->
          <div v-else class="search-panel-hint">
            <div class="search-panel-hint-row">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
              <span>搜索文献标题、作者、摘要、关键词</span>
            </div>
            <div class="search-panel-hint-row">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
              </svg>
              <span>搜索笔记标题和内容</span>
            </div>
            <div class="search-panel-hint-row">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              <span>搜索分组名称</span>
            </div>
          </div>

          <!-- 底部快捷键提示 -->
          <div class="search-panel-footer">
            <span class="search-panel-key-hint"><kbd>↑</kbd><kbd>↓</kbd><span>导航</span></span>
            <span class="search-panel-key-hint"><kbd>Enter</kbd><span>跳转</span></span>
            <span class="search-panel-key-hint"><kbd>Esc</kbd><span>关闭</span></span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
